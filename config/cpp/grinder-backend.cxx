#include "grinder-backend.hxx"
#include "linuxcnc/emc.hh"
#include "linuxcnc/nml.hh"
#include "linuxcnc/rcs.hh"
#include "linuxcnc/stat_msg.hh"
#include "nmlmsg.hh"
#include "settings.hxx"
#include "shcom.hh"
#include <cassert>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <cxxabi.h>
#include <execinfo.h>
#include <iostream>
#include <libunwind.h>
#include <sstream>

#ifndef EMC2_DEFAULT_INIFILE
#define EMC2_DEFAULT_INIFILE "/usr/share/linuxcnc/linuxcnc.ini"
#endif

#define UNUSED(x) (void)(x)

GrinderMotion::GrinderMotion(SettingsManager *aSettingsManager)
	: is_running(false), machine_ok(false), grinder_should_monitor(true), mySettingsManager(aSettingsManager)
{
	if (aSettingsManager == nullptr)
	{
		std::cerr << "SettingsManager is null!\n";
		exit(1);
	}
}

void GrinderMotion::monitorState()
{
	std::this_thread::sleep_for(std::chrono::milliseconds(1000));

	for (int i = 0; i < 10; ++i)
	{
		updateStatus();
		myEmcStatus = emcStatusGet();
		if (myEmcStatus == nullptr)
		{
			std::cerr << "EMC status is null! Linuxcnc is probably not fully up yet, retrying!\n";
			// cleanup();
			// exit(1);
			std::this_thread::sleep_for(std::chrono::milliseconds(500));
			continue;
		}
		else
		{
			std::cout << "EMC is online!\n";
			break;
		}
	}

	std::cout << "Monitoring state\n";
	while (grinder_should_monitor)
	{
		monitorStateImpl();
		std::this_thread::sleep_for(std::chrono::milliseconds(5));
		mainSequence();
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	}
}

bool GrinderMotion::checkErrors()
{
	// Wait for previous commands to complete and check for errors
	while (error_channel->get_queue_length() > 0)
	{
		NMLTYPE type = error_channel->read();
		if (type != 0)
		{
			std::cerr << "Error executing command: " << type << '\n';
			return false;
		}
	}

	return true;
}

bool GrinderMotion::sendCommand(NMLmsg &msg)
{
	if (command_channel->write(msg) != 0)
	{
		std::cerr << "Failed to send command\n";
		return false;
	}

	return checkErrors();
}

// Add MDI mode checking and proper command execution waiting
bool GrinderMotion::setMDIMode()
{

	sendMdi();

	return true;
}

void GrinderMotion::monitorStateImpl()
{

	auto updated = updateStatus();
	if (updated < 0)
	{
		std::cerr << "Error updating status: " << " \n";
		std::this_thread::sleep_for(std::chrono::milliseconds(1000));
		return;
	}

	updated = updateError();

	if (updated < 0)
	{
		std::cerr << "Error updating error: " << " \n";
		std::this_thread::sleep_for(std::chrono::milliseconds(1000));
		return;
	}

	if (*grinder_pins->requires_save)
	{
		std::cout << "GUI requested settings to be saved, saving...\n";
		mySettingsManager->Save();
		*(grinder_pins->requires_save) = false;
	}

	updateStatus();

	bool was_ok = machine_ok.load();
	bool is_ok = !(myEmcStatus->task.state == EMC_TASK_STATE_ESTOP) &&
				 myEmcStatus->task.state == EMC_TASK_STATE_ON &&
				 myEmcStatus->motion.traj.enabled;

	// Update position

	current_pos[0] = myEmcStatus->motion.traj.position.tran.x;
	current_pos[1] = myEmcStatus->motion.traj.position.tran.y;
	current_pos[2] = myEmcStatus->motion.traj.position.tran.z;

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
}

void GrinderMotion::Start()
{
	try
	{
		// Initialize HAL first but don't mark ready
		initializeHAL();

		// Initialize NML
		initializeNML();

		// std::cout << "NML initialized\n";

		// Only mark HAL ready after all initialization is complete
		if (hal_ready(hal_comp_id) != 0)
		{
			throw std::runtime_error("Failed to mark HAL component as ready");
		}

		std::cout << "HAL component ready\n";
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

GrinderMotion::~GrinderMotion() { cleanup(); }

void GrinderMotion::initializeNML()
{

	assert(tryNml(10, 2) >= 0);
	updateStatus();
	std::cout << "EMC status address: " << myEmcStatus << '\n';

	// Set initial mode to manual
	setMDIMode();
}

void GrinderMotion::initializeHAL()
{
	// Use a unique name for loadusr
	const char *comp_name = "grinder";

	// Initialize with number of pins we'll create
	hal_comp_id = hal_init(comp_name);

	if (hal_comp_id < 0)
	{
		std::cout << "Failed to initialize HAL component" << std::to_string(hal_comp_id) << "\n";
		throw std::runtime_error("Failed to initialize HAL component: " + std::to_string(hal_comp_id));
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
	hal_pin_float_new((prefix + "dress_start_x").c_str(), HAL_IO, &(grinder_pins->dress_start_x), hal_comp_id);
	hal_pin_float_new((prefix + "dress_start_y").c_str(), HAL_IO, &(grinder_pins->dress_start_y), hal_comp_id);
	hal_pin_float_new((prefix + "dress_start_z").c_str(), HAL_IO, &(grinder_pins->dress_start_z), hal_comp_id);
	hal_pin_float_new((prefix + "dress_end_x").c_str(), HAL_IO, &(grinder_pins->dress_end_x), hal_comp_id);
	hal_pin_float_new((prefix + "dress_end_y").c_str(), HAL_IO, &(grinder_pins->dress_end_y), hal_comp_id);
	hal_pin_float_new((prefix + "dress_end_z").c_str(), HAL_IO, &(grinder_pins->dress_end_z), hal_comp_id);
	hal_pin_float_new((prefix + "dress_stepover_x").c_str(), HAL_IO, &(grinder_pins->dress_stepover_x), hal_comp_id);
	hal_pin_float_new((prefix + "dress_stepover_y").c_str(), HAL_IO, &(grinder_pins->dress_stepover_y), hal_comp_id);
	hal_pin_float_new((prefix + "dress_stepover_z").c_str(), HAL_IO, &(grinder_pins->dress_stepover_z), hal_comp_id);
	hal_pin_float_new((prefix + "dress_wheel_rpm").c_str(), HAL_IO, &(grinder_pins->dress_wheel_rpm), hal_comp_id);
	hal_pin_float_new((prefix + "dress_wheel_dia").c_str(), HAL_IO, &(grinder_pins->dress_wheel_dia), hal_comp_id);
	hal_pin_float_new((prefix + "dress_point_dia").c_str(), HAL_IO, &(grinder_pins->dress_point_dia), hal_comp_id);
	hal_pin_s32_new((prefix + "dress_offset_gcode").c_str(), HAL_IO, &(grinder_pins->dress_offset_gcode), hal_comp_id);
	hal_pin_bit_new((prefix + "downfeed_now").c_str(), HAL_IO, &(grinder_pins->downfeed_now), hal_comp_id);
	hal_pin_bit_new((prefix + "requires_save").c_str(), HAL_IO, &(grinder_pins->requires_save), hal_comp_id);
	std::cout << "HAL pins initialized\n";

	// Initialize default values - note the dereferencing
	*(grinder_pins->z_direction) = true;
	*(grinder_pins->downfeed_now) = false;
	*(grinder_pins->is_running) = false;
	*(grinder_pins->requires_save) = false;

	auto settings = mySettingsManager->Get();
	*(grinder_pins->x_min) = settings->x_min;
	*(grinder_pins->x_max) = settings->x_max;
	*(grinder_pins->y_min) = settings->y_min;
	*(grinder_pins->y_max) = settings->y_max;
	*(grinder_pins->z_min) = settings->z_min;
	*(grinder_pins->z_max) = settings->z_max;
	*(grinder_pins->x_speed) = settings->x_speed;
	*(grinder_pins->y_speed) = settings->y_speed;
	*(grinder_pins->z_speed) = settings->z_speed;
	*(grinder_pins->z_crossfeed) = settings->z_crossfeed;
	*(grinder_pins->y_downfeed) = settings->y_downfeed;
	*(grinder_pins->enable_x) = settings->enable_x;
	*(grinder_pins->enable_y) = settings->enable_y;
	*(grinder_pins->enable_z) = settings->enable_z;
	*(grinder_pins->stop_at_z_limit) = settings->stop_at_z_limit;
	*(grinder_pins->crossfeed_at) = settings->crossfeed_at;
	*(grinder_pins->repeat_at) = settings->repeat_at;
	*(grinder_pins->dress_start_x) = settings->dress_start_x;
	*(grinder_pins->dress_start_y) = settings->dress_start_y;
	*(grinder_pins->dress_start_z) = settings->dress_start_z;
	*(grinder_pins->dress_end_x) = settings->dress_end_x;
	*(grinder_pins->dress_end_y) = settings->dress_end_y;
	*(grinder_pins->dress_end_z) = settings->dress_end_z;
	*(grinder_pins->dress_stepover_x) = settings->dress_stepover_x;
	*(grinder_pins->dress_stepover_y) = settings->dress_stepover_y;
	*(grinder_pins->dress_stepover_z) = settings->dress_stepover_z;
	*(grinder_pins->dress_wheel_rpm) = settings->dress_wheel_rpm;
	*(grinder_pins->dress_wheel_dia) = settings->dress_wheel_dia;
}

void GrinderMotion::sendMDICommand(const char *command)
{
	std::cout << "Sending MDI command: " << command << '\n';
	sendMdiCmd(command);
}

bool GrinderMotion::canStart()
{
	updateStatus();
	auto stateEstop = (myEmcStatus->task.state == EMC_TASK_STATE_ESTOP);
	auto powerOff = (myEmcStatus->task.state == EMC_TASK_STATE_OFF);
	auto motion_enabled = myEmcStatus->motion.traj.enabled;

	return (!stateEstop && !powerOff && motion_enabled);
}

void GrinderMotion::start()
{
	std::cout << "Starting grinder\n";
	if (!is_running && canStart())
	{
		std::cout << "Starting grinder thread\n";
		is_running = true;
		*(grinder_pins->is_running) = true;
		// main_thread = std::thread(&GrinderMotion::mainSequence, this);
	}
	else
	{
		std::cout << "Grinder cannot start, check estop and power\n";
		*(grinder_pins->is_running) = false;
	}
}

void GrinderMotion::stop()
{
	if (is_running)
	{
		is_running = false;
		*(grinder_pins->is_running) = false;
		// if (main_thread.joinable())
		// {
		// 	std::cout << "Joining main thread\n";
		// 	main_thread.join();
		// 	std::cout << "Main thread joined\n";
		// }

		// EMC_TASK_ABORT abortMsg;
		// command_channel->write(abortMsg);
	}
}

void GrinderMotion::moveInsideLimits()
{
	// Use HAL pin values directly since they're updated by monitor thread
	if (current_pos[0] > *(grinder_pins->x_max) && *(grinder_pins->enable_x))
	{
		std::cout << "X position is greater than max, moving to x_max\n";
		std::stringstream ss;
		ss << "G1 X" << *(grinder_pins->x_min) << " F" << *(grinder_pins->x_speed);
		sendMDICommand(ss.str().c_str());
	}
	if (current_pos[0] < *(grinder_pins->x_min) && *(grinder_pins->enable_x))
	{
		std::cout << "X position is less than min, moving to x_min\n";
		std::stringstream ss;
		ss << "G1 X" << *(grinder_pins->x_max) << " F" << *(grinder_pins->x_speed);
		sendMDICommand(ss.str().c_str());
	}

	// Check Y axis limits
	if (current_pos[1] > *(grinder_pins->y_max) && *(grinder_pins->enable_y))
	{
		std::cout << "Y position is greater than max, moving to y_max\n";
		std::stringstream ss;
		ss << "G1 Y" << *(grinder_pins->y_min) << " F" << *(grinder_pins->y_speed);
		sendMDICommand(ss.str().c_str());
	}
	if (current_pos[1] < *(grinder_pins->y_min) && *(grinder_pins->enable_y))
	{
		std::cout << "Y position is less than min, moving to y_min\n";
		std::stringstream ss;
		ss << "G1 Y" << *(grinder_pins->y_max) << " F" << *(grinder_pins->y_speed);
		sendMDICommand(ss.str().c_str());
	}

	// Check Z axis limits
	if (current_pos[2] > *(grinder_pins->z_max) && *(grinder_pins->enable_z))
	{
		std::cout << "Z position is greater than max, moving to z_max\n";
		std::stringstream ss;
		ss << "G1 Z" << *(grinder_pins->z_min) << " F" << *(grinder_pins->z_speed);
		sendMDICommand(ss.str().c_str());
	}
	if (current_pos[2] < *(grinder_pins->z_min) && *(grinder_pins->enable_z))
	{
		std::cout << "Z position is less than min, moving to z_min\n";
		std::stringstream ss;
		ss << "G1 Z" << *(grinder_pins->z_max) << " F" << *(grinder_pins->z_speed);
		sendMDICommand(ss.str().c_str());
	}

	waitForMotionComplete();
}

void GrinderMotion::waitForMotionComplete()
{
	emcCommandWaitDone();
	std::cout << "Motion complete\n";
}

void GrinderMotion::downfeed()
{
	std::cout << "Downfeed\n";
	std::stringstream ss;
	// Get current Y position
	double y_pos = current_pos[2];
	// double y_max = *(grinder_pins->y_max);
	double y_min = *(grinder_pins->y_min);
	double y_downfeed = *(grinder_pins->y_downfeed);
	double new_y_pos = y_pos - y_downfeed;
	if (new_y_pos < y_min)
	{
		*(grinder_pins->y_min) = new_y_pos;
	}
	ss << "G1 Z" << *(grinder_pins->z_min) << " F" << *(grinder_pins->z_speed);
	sendMDICommand(ss.str().c_str());
	waitForMotionComplete();
	*(grinder_pins->downfeed_now) = false;
}

void GrinderMotion::mainSequence()
{

	if (!machine_ok.load())
	{
		std::cout << "Machine not ok\n";
		return;
	}

	if (*(grinder_pins->downfeed_now))
	{
		std::cout << "Downfeed now\n";
		if (!*(grinder_pins->is_running))
		{
			if (!setMDIMode())
			{
				std::cerr << "Failed to set MDI mode\n";
				stop();
				return;
			}
			waitForMotionComplete();
		}
		downfeed();
	}

	if (!*(grinder_pins->is_running) || !machine_ok.load())
	{
		return;
	}

	if (is_first_run)
	{
		is_first_run = false;
		std::cout << "Ensuring MDI mode is set\n";
		if (!setMDIMode())
		{
			std::cerr << "Failed to set MDI mode\n";
			stop();
			return;
		}
		waitForMotionComplete();

		moveInsideLimits();

		waitForMotionComplete();
	}

	updateStatus();

	// Update is_running pin based on external changes
	if (!(*(grinder_pins->is_running)))
	{
		stop();
		return;
	}

	std::cout << "o<xmove_to_max> call\n";
	sendMDICommand("o<xmove_to_max> call");
	waitForMotionComplete();
	sendMDICommand("o<xmove_to_max> call");
	waitForMotionComplete();

	if (!machine_ok.load())
	{
		return;
	}

	std::cout << "o<xmove_to_min> call\n";
	sendMDICommand("o<xmove_to_min> call");
	waitForMotionComplete();

	std::this_thread::sleep_for(std::chrono::milliseconds(500));

	if (!*(grinder_pins->is_running))
	{
		stop();
	}
}

// Make these public for external access
[[nodiscard]] bool GrinderMotion::getIsRunning() const { return is_running; }
// [[nodiscard]] hal_bit_t GrinderMotion::getIsRunningPin() const { return *(grinder_pins->is_running); }

// Add a clean shutdown method
void GrinderMotion::cleanup()
{
	if (is_running)
	{
		stop();
	}

	is_running = false;
	grinder_should_monitor = false;
	// if (main_thread.joinable())
	// {
	// 	main_thread.join();
	// }

	// if (monitor_thread.joinable())
	// {
	// 	monitor_thread.join();
	// }

	if (hal_comp_id > 0)
	{
		// Free allocated memory
		std::cout << "exiting hal component\n";
		hal_exit(hal_comp_id);
	}

	// delete command_channel;
	// delete error_channel;
	// delete stat_channel;
}