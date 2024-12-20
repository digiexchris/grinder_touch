#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <iostream>
#include <signal.h>
#include <sstream> // Add this with the other includes at the top
#include <thread>

// LinuxCNC includes
#include "linuxcnc/emc.hh"
#include "linuxcnc/emc_nml.hh"
#include "linuxcnc/hal.h"
#include "linuxcnc/nml.hh"
#include "linuxcnc/rcs.hh" // For NML buffer types
#include "linuxcnc/stat_msg.hh"

// Define missing constants if not provided by headers
#ifndef EMC2_DEFAULT_INIFILE
#define EMC2_DEFAULT_INIFILE "/usr/share/linuxcnc/linuxcnc.ini"
#endif

// Define NML config file path
const char *const DEFAULT_NMLFILE = "/usr/share/linuxcnc/linuxcnc.nml";

#define UNUSED(x) (void)(x)

struct GrinderPins
{
	// Change all members to pointers
	hal_float_t *x_min, *x_max, *y_min, *y_max, *z_min, *z_max;
	hal_float_t *x_speed, *y_speed, *z_speed;
	hal_bit_t *z_direction, *enable_x, *enable_y, *enable_z;
	hal_bit_t *stop_at_z_limit, *is_running;
	hal_float_t *z_crossfeed, *y_downfeed;
	hal_s32_t *crossfeed_at, *repeat_at;
};

class GrinderMotion
{
private:
	RCS_STAT_CHANNEL *stat_channel;
	EMC_STAT *emcStatus;
	NML *error_channel;
	NML *command_channel;
	std::atomic<bool> is_running;
	std::atomic<bool> machine_ok;
	std::thread main_thread;
	std::thread monitor_thread;
	int hal_comp_id;
	GrinderPins *grinder_pins;

	bool grinder_should_monitor = true;

	std::array<double, 9> current_pos;

	static void monitorState(GrinderMotion *self)
	{
		self->monitorStateImpl();
	}

	void monitorStateImpl()
	{
		std::cout << "Monitoring state\n";
		while (grinder_should_monitor)
		{
			stat_channel->peek();

			bool was_ok = machine_ok.load();
			bool is_ok = !(emcStatus->task.state == EMC_TASK_STATE_ESTOP) &&
						 emcStatus->task.state == EMC_TASK_STATE_ON &&
						 emcStatus->motion.traj.enabled;

			// std::cout << "Task state: " << emcStatus->task.state << '\n';
			// std::cout << "Motion enabled: " << emcStatus->motion.traj.enabled << '\n';
			// std::cout << "Machine OK: " << is_ok << '\n';

			// Update position

			current_pos[0] = emcStatus->motion.traj.position.tran.x;
			current_pos[1] = emcStatus->motion.traj.position.tran.y;
			current_pos[2] = emcStatus->motion.traj.position.tran.z;

			std::cout << "Current position: " << current_pos[0] << ", " << current_pos[1] << ", " << current_pos[2] << '\n';

			// Check for state changes

			if (was_ok != is_ok)
			{
				machine_ok.store(is_ok);
				if (!is_ok && is_running)
				{
					std::cout << "Stopping grinding cycle\n";
					stop();
				}
			}

			if (*(grinder_pins->is_running) && !is_running)
			{
				std::cout << "Starting grinding cycle\n";
				start();
			}

			// Check for errors
			if (error_channel != nullptr)
			{
				NMLTYPE type = error_channel->read();
				if (type != 0)
				{
					std::cerr << "Error type: " << type << " - ";
					switch (type)
					{
					case EMC_OPERATOR_ERROR_TYPE:
						std::cerr << "Operator Error";
						break;
					case EMC_OPERATOR_TEXT_TYPE:
						std::cerr << "Operator Info";
						break;
					case EMC_OPERATOR_DISPLAY_TYPE:
						std::cerr << "Operator Display";
						break;
					default:
						std::cerr << "Unknown";
					}
					std::cerr << '\n';
				}
			}

			std::cout << "Grinder is running: " << *(grinder_pins->is_running) << '\n';
			std::cout << "x_min: " << *(grinder_pins->x_min) << '\n';

			std::cout << "Sleeping for 1 second\n";

			std::this_thread::sleep_for(std::chrono::milliseconds(1000));
		}

		std::cout << "State monitoring thread exiting\n";
	}

	// Add this new method
	void waitForMotionComplete()
	{
		while (is_running && machine_ok.load())
		{
			stat_channel->peek();

			if (emcStatus->motion.status == RCS_DONE)
			{
				return;
			}

			if (emcStatus->motion.status == RCS_ERROR)
			{
				std::cerr << "Motion error detected\n";
				stop();
				return;
			}

			std::this_thread::sleep_for(std::chrono::milliseconds(10));
		}
	}

public:
	GrinderMotion() : is_running(false), machine_ok(false)
	{
		try
		{
			// Initialize HAL first but don't mark ready
			initializeHAL();
			// Initialize NML
			initializeNML();

			// Only mark HAL ready after all initialization is complete
			if (hal_ready(hal_comp_id) != 0)
			{
				throw std::runtime_error("Failed to mark HAL component as ready");
			}

			std::cout << "HAL component ready\n";

			// Start state monitoring thread
			monitor_thread = std::thread(GrinderMotion::monitorState, this);

			std::cout << "State monitoring thread started\n";
		}
		catch (const std::exception &e)
		{
			std::cerr << "Initialization error: " << e.what() << '\n';
			std::cout << "Initialization error: " << e.what() << '\n';
			if (hal_comp_id > 0)
			{
				hal_exit(hal_comp_id);
				exit(1);
			}
			throw;
		}
	}

	~GrinderMotion() { cleanup(); }

	void initializeNML()
	{
		// Create NML channels directly
		command_channel = new NML(0, "emcCommand", "xemc", DEFAULT_NMLFILE);
		if ((command_channel == nullptr) || (command_channel->valid() == 0))
		{
			throw std::runtime_error("Can't open command channel");
		}

		std::cout << "Command channel opened\n";

		stat_channel =
			new RCS_STAT_CHANNEL(0, "emcStatus", "xemc", DEFAULT_NMLFILE);
		if ((stat_channel == nullptr) || (stat_channel->valid() == 0))
		{
			throw std::runtime_error("Can't open status channel");
		}

		std::cout << "Status channel opened\n";

		error_channel = new NML(0, "emcError", "xemc", DEFAULT_NMLFILE);
		if ((error_channel == nullptr) || (error_channel->valid() == 0))
		{
			throw std::runtime_error("Can't open error channel");
		}

		std::cout << "Error channel opened\n";

		emcStatus = static_cast<EMC_STAT *>(stat_channel->get_address());

		std::cout << "EMC status address: " << emcStatus << '\n';

		// Set initial mode to manual
		EMC_TASK_SET_MODE mode_msg;
		mode_msg.mode = EMC_TASK_MODE_MANUAL;
		command_channel->write(mode_msg);

		std::cout << "EMC mode set to manual\n";
	}

	void initializeHAL()
	{
		// Use a unique name for loadusr
		const char *comp_name = "grinder";

		// Initialize with number of pins we'll create
		hal_comp_id = hal_init(comp_name);

		if (hal_comp_id < 0)
		{
			throw std::runtime_error("Failed to initialize HAL component");
		}

		grinder_pins = static_cast<GrinderPins *>(hal_malloc(sizeof(GrinderPins)));
		if (grinder_pins == nullptr)
		{
			throw std::runtime_error("Failed to allocate HAL shared memory");
		}

		// Create pins with component prefix
		const std::string prefix = std::string(comp_name) + ".";

		// Create the pins - note we're not casting the addresses anymore
		hal_pin_float_new((prefix + "x_min").c_str(), HAL_IN, &(grinder_pins->x_min), hal_comp_id);
		hal_pin_float_new((prefix + "x_max").c_str(), HAL_IN, &(grinder_pins->x_max), hal_comp_id);
		hal_pin_float_new((prefix + "y_min").c_str(), HAL_IN, &(grinder_pins->y_min), hal_comp_id);
		hal_pin_float_new((prefix + "y_max").c_str(), HAL_IN, &(grinder_pins->y_max), hal_comp_id);
		hal_pin_float_new((prefix + "z_min").c_str(), HAL_IN, &(grinder_pins->z_min), hal_comp_id);
		hal_pin_float_new((prefix + "z_max").c_str(), HAL_IN, &(grinder_pins->z_max), hal_comp_id);
		hal_pin_float_new((prefix + "x_speed").c_str(), HAL_IN, &(grinder_pins->x_speed), hal_comp_id);
		hal_pin_float_new((prefix + "y_speed").c_str(), HAL_IN, &(grinder_pins->y_speed), hal_comp_id);
		hal_pin_float_new((prefix + "z_speed").c_str(), HAL_IN, &(grinder_pins->z_speed), hal_comp_id);
		hal_pin_bit_new((prefix + "z_direction").c_str(), HAL_IO, &(grinder_pins->z_direction), hal_comp_id);
		hal_pin_float_new((prefix + "z_crossfeed").c_str(), HAL_IN, &(grinder_pins->z_crossfeed), hal_comp_id);
		hal_pin_float_new((prefix + "y_downfeed").c_str(), HAL_IN, &(grinder_pins->y_downfeed), hal_comp_id);
		hal_pin_bit_new((prefix + "enable_x").c_str(), HAL_IO, &(grinder_pins->enable_x), hal_comp_id);
		hal_pin_bit_new((prefix + "enable_y").c_str(), HAL_IO, &(grinder_pins->enable_y), hal_comp_id);
		hal_pin_bit_new((prefix + "enable_z").c_str(), HAL_IO, &(grinder_pins->enable_z), hal_comp_id);
		hal_pin_bit_new((prefix + "stop_at_z_limit").c_str(), HAL_IN, &(grinder_pins->stop_at_z_limit), hal_comp_id);
		hal_pin_s32_new((prefix + "crossfeed_at").c_str(), HAL_IN, &(grinder_pins->crossfeed_at), hal_comp_id);
		hal_pin_s32_new((prefix + "repeat_at").c_str(), HAL_IN, &(grinder_pins->repeat_at), hal_comp_id);
		hal_pin_bit_new((prefix + "is_running").c_str(), HAL_IO, &(grinder_pins->is_running), hal_comp_id);

		std::cout << "HAL pins initialized\n";

		// Initialize default values - note the dereferencing
		*(grinder_pins->z_direction) = true;
		*(grinder_pins->is_running) = false;
	}

	void sendMDICommand(const char *command)
	{
		EMC_TASK_PLAN_EXECUTE msg;
		msg.command[0] = 0;
		strncpy(msg.command, command, sizeof(msg.command) - 1);
		command_channel->write(msg);
	}

	bool canStart()
	{
		stat_channel->peek();
		return !(emcStatus->task.state == EMC_TASK_STATE_ESTOP) &&
			   emcStatus->task.state == EMC_TASK_STATE_ON &&
			   emcStatus->motion.traj.enabled;
	}

	void start()
	{
		if (!is_running && canStart())
		{
			is_running = true;
			*(grinder_pins->is_running) = true;
			main_thread = std::thread(&GrinderMotion::mainSequence, this);
		}
	}

	void stop()
	{
		if (is_running)
		{
			is_running = false;
			*(grinder_pins->is_running) = false;
			if (main_thread.joinable())
			{
				main_thread.join();
			}

			EMC_TASK_ABORT abortMsg;
			command_channel->write(abortMsg);
		}
	}

	void moveInsideLimits()
	{
		// Use HAL pin values directly since they're updated by monitor thread
		if (current_pos[0] > *(grinder_pins->x_max) && *(grinder_pins->enable_x))
		{
			std::stringstream ss;
			ss << "G1 X" << *(grinder_pins->x_min) << " F" << *(grinder_pins->x_speed);
			sendMDICommand(ss.str().c_str());
		}
		if (current_pos[0] < *(grinder_pins->x_min) && *(grinder_pins->enable_x))
		{
			std::stringstream ss;
			ss << "G1 X" << *(grinder_pins->x_max) << " F" << *(grinder_pins->x_speed);
			sendMDICommand(ss.str().c_str());
		}

		// Check Y axis limits
		if (current_pos[1] > *(grinder_pins->y_max) && *(grinder_pins->enable_y))
		{
			std::stringstream ss;
			ss << "G1 Y" << *(grinder_pins->y_min) << " F" << *(grinder_pins->y_speed);
			sendMDICommand(ss.str().c_str());
		}
		if (current_pos[1] < *(grinder_pins->y_min) && *(grinder_pins->enable_y))
		{
			std::stringstream ss;
			ss << "G1 Y" << *(grinder_pins->y_max) << " F" << *(grinder_pins->y_speed);
			sendMDICommand(ss.str().c_str());
		}

		// Check Z axis limits
		if (current_pos[2] > *(grinder_pins->z_max) && *(grinder_pins->enable_z))
		{
			std::stringstream ss;
			ss << "G1 Z" << *(grinder_pins->z_min) << " F" << *(grinder_pins->z_speed);
			sendMDICommand(ss.str().c_str());
		}
		if (current_pos[2] < *(grinder_pins->z_min) && *(grinder_pins->enable_z))
		{
			std::stringstream ss;
			ss << "G1 Z" << *(grinder_pins->z_max) << " F" << *(grinder_pins->z_speed);
			sendMDICommand(ss.str().c_str());
		}

		waitForMotionComplete();
	}

	void mainSequence()
	{
		EMC_TASK_SET_MODE modeMsg;
		modeMsg.mode = EMC_TASK_MODE_MDI;
		command_channel->write(modeMsg);

		while (*(grinder_pins->is_running) && machine_ok.load())
		{
			stat_channel->peek();

			// Update is_running pin based on external changes
			if (!(*(grinder_pins->is_running)))
			{
				stop();
				return;
			}

			moveInsideLimits();

			std::cout << "o<xmove_to_max> call\n";
			sendMDICommand("o<xmove_to_max> call");
			waitForMotionComplete();

			if (!machine_ok.load())
			{
				break;
			}

			std::cout << "o<xmove_to_min> call\n";
			sendMDICommand("o<xmove_to_min> call");
			waitForMotionComplete();

			std::this_thread::sleep_for(std::chrono::milliseconds(5));
		}

		if (*(grinder_pins->is_running))
		{
			stop();
			return;
		}
	}

	// Make these public for external access
	[[nodiscard]] bool getIsRunning() const { return is_running; }
	[[nodiscard]] hal_bit_t getIsRunningPin() const { return *(grinder_pins->is_running); }

	// Add a clean shutdown method
	void cleanup()
	{
		stop();
		is_running = false;
		grinder_should_monitor = false;
		if (main_thread.joinable())
		{
			main_thread.join();
		}

		if (monitor_thread.joinable())
		{
			monitor_thread.join();
		}

		if (hal_comp_id > 0)
		{
			// Free allocated memory
			hal_exit(hal_comp_id);
		}

		delete command_channel;
		delete error_channel;
		delete stat_channel;
	}
};

static GrinderMotion *grinder = nullptr;

void signal_handler(int sig)
{
	std::cout << "Signal received: " << sig << "\n";
	if (grinder != nullptr)
	{
		grinder->cleanup();
		delete grinder;
		grinder = nullptr;
	}
	exit(sig);
}

int main(int argc, char **argv)
{
	if (argc > 1)
	{
		// If INI file specified on command line, set it in environment
		setenv("INI_FILE_NAME", argv[1], 1);
	}

	signal(SIGINT, signal_handler);
	signal(SIGTERM, signal_handler);
	signal(SIGPIPE, signal_handler); // Add SIGPIPE handling for HAL communication
	signal(SIGQUIT, signal_handler); // Add handler for Ctrl-C (SIGQUIT)

	try
	{
		grinder = new GrinderMotion();

		// Main loop with shorter sleep time for better responsiveness
		while (true)
		{

			std::this_thread::sleep_for(std::chrono::milliseconds(50));
		}
	}
	catch (const std::exception &e)
	{
		std::cerr << "Error: " << e.what() << '\n';
		if (grinder != nullptr)
		{
			grinder->cleanup();
			delete grinder;
		}
		return 1;
	}

	return 0;
}
