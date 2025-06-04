#include "grinder_motion_gui.hxx"
#include "linuxcnc/emc.hh"
#include "linuxcnc/nml.hh"
#include "linuxcnc/rcs.hh"
#include "linuxcnc/stat_msg.hh"
#include "nmlmsg.hh"
#include "shcom.hh"
#include <cassert>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sstream>

#ifndef EMC2_DEFAULT_INIFILE
#define EMC2_DEFAULT_INIFILE "/usr/share/linuxcnc/linuxcnc.ini"
#endif

#define UNUSED(x) (void)(x)

GrinderMotionGui::GrinderMotionGui(SettingsManager *aSettingsManager)
	: is_running(false), machine_ok(false), grinder_should_monitor(true), mySettingsManager(aSettingsManager),
	  is_first_run(true), downfeed_now(false)
{
	if (aSettingsManager == nullptr)
	{
		std::cerr << "SettingsManager is null!\n";
		throw std::runtime_error("SettingsManager cannot be null");
	}

	// Initialize settings from file
	loadSettings();
}

GrinderMotionGui::~GrinderMotionGui()
{
	cleanup();
}

void GrinderMotionGui::loadSettings()
{
	auto settings = mySettingsManager->Get();
	grinder_settings.x_min = settings->x_min;
	grinder_settings.x_max = settings->x_max;
	grinder_settings.y_min = settings->y_min;
	grinder_settings.y_max = settings->y_max;
	grinder_settings.z_min = settings->z_min;
	grinder_settings.z_max = settings->z_max;
	grinder_settings.x_speed = settings->x_speed;
	grinder_settings.y_speed = settings->y_speed;
	grinder_settings.z_speed = settings->z_speed;
	grinder_settings.z_crossfeed = settings->z_crossfeed;
	grinder_settings.y_downfeed = settings->y_downfeed;
	grinder_settings.enable_x = settings->enable_x;
	grinder_settings.enable_y = settings->enable_y;
	grinder_settings.enable_z = settings->enable_z;
	grinder_settings.stop_at_z_limit = settings->stop_at_z_limit;
	grinder_settings.crossfeed_at = settings->crossfeed_at;
	grinder_settings.repeat_at = settings->repeat_at;
	grinder_settings.dress_start_x = settings->dress_start_x;
	grinder_settings.dress_start_y = settings->dress_start_y;
	grinder_settings.dress_start_z = settings->dress_start_z;
	grinder_settings.dress_end_x = settings->dress_end_x;
	grinder_settings.dress_end_y = settings->dress_end_y;
	grinder_settings.dress_end_z = settings->dress_end_z;
	grinder_settings.dress_stepover_x = settings->dress_stepover_x;
	grinder_settings.dress_stepover_y = settings->dress_stepover_y;
	grinder_settings.dress_stepover_z = settings->dress_stepover_z;
	grinder_settings.dress_wheel_rpm = settings->dress_wheel_rpm;
	grinder_settings.dress_wheel_dia = settings->dress_wheel_dia;
}

void GrinderMotionGui::saveSettings()
{
	auto settings = mySettingsManager->Get();
	settings->x_min = grinder_settings.x_min;
	settings->x_max = grinder_settings.x_max;
	settings->y_min = grinder_settings.y_min;
	settings->y_max = grinder_settings.y_max;
	settings->z_min = grinder_settings.z_min;
	settings->z_max = grinder_settings.z_max;
	settings->x_speed = grinder_settings.x_speed;
	settings->y_speed = grinder_settings.y_speed;
	settings->z_speed = grinder_settings.z_speed;
	settings->z_crossfeed = grinder_settings.z_crossfeed;
	settings->y_downfeed = grinder_settings.y_downfeed;
	settings->enable_x = grinder_settings.enable_x;
	settings->enable_y = grinder_settings.enable_y;
	settings->enable_z = grinder_settings.enable_z;
	settings->stop_at_z_limit = grinder_settings.stop_at_z_limit;
	settings->crossfeed_at = grinder_settings.crossfeed_at;
	settings->repeat_at = grinder_settings.repeat_at;
	settings->dress_start_x = grinder_settings.dress_start_x;
	settings->dress_start_y = grinder_settings.dress_start_y;
	settings->dress_start_z = grinder_settings.dress_start_z;
	settings->dress_end_x = grinder_settings.dress_end_x;
	settings->dress_end_y = grinder_settings.dress_end_y;
	settings->dress_end_z = grinder_settings.dress_end_z;
	settings->dress_stepover_x = grinder_settings.dress_stepover_x;
	settings->dress_stepover_y = grinder_settings.dress_stepover_y;
	settings->dress_stepover_z = grinder_settings.dress_stepover_z;
	settings->dress_wheel_rpm = grinder_settings.dress_wheel_rpm;
	settings->dress_wheel_dia = grinder_settings.dress_wheel_dia;
	mySettingsManager->Save();
	std::cout << "Settings saved\n";
}

void GrinderMotionGui::Start()
{
	// Initialize LinuxCNC NML connections without HAL
	for (int i = 0; i < 10; ++i)
	{
		updateStatus();
		myEmcStatus = emcStatusGet();
		if (myEmcStatus == nullptr)
		{
			std::cerr << "EMC status is null! LinuxCNC is probably not fully up yet, retrying!\n";
			std::this_thread::sleep_for(std::chrono::milliseconds(500));
			continue;
		}
		else
		{
			std::cout << "EMC is online!\n";
			break;
		}
	}

	// Initialize NML
	initializeNML();
}

void GrinderMotionGui::initializeNML()
{
	assert(tryNml(10, 2) >= 0);
	updateStatus();
	std::cout << "EMC status address: " << myEmcStatus << '\n';

	// Set initial mode to manual
	setMDIMode();
}

bool GrinderMotionGui::checkErrors()
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

bool GrinderMotionGui::sendCommand(NMLmsg &msg)
{
	if (command_channel->write(msg) != 0)
	{
		std::cerr << "Failed to send command\n";
		return false;
	}
	return checkErrors();
}

bool GrinderMotionGui::setMDIMode()
{
	sendMdi();
	return true;
}

void GrinderMotionGui::sendMDICommand(const char *command)
{
	if (!command)
	{
		std::cerr << "Command is null!\n";
		return;
	}

	std::cout << "Sending MDI command: " << command << std::endl;

	EMC_TASK_PLAN_EXECUTE taskPlanExecute;
	strcpy(taskPlanExecute.command, command);
	sendCommand(taskPlanExecute);
}

bool GrinderMotionGui::canStart()
{
	if (myEmcStatus == nullptr)
	{
		return false;
	}

	return !(myEmcStatus->task.state == EMC_TASK_STATE_ESTOP) &&
		   myEmcStatus->task.state == EMC_TASK_STATE_ON &&
		   myEmcStatus->motion.traj.enabled;
}

void GrinderMotionGui::waitForMotionComplete()
{
	if (myEmcStatus == nullptr)
	{
		return;
	}

	while (myEmcStatus->motion.traj.queue > 0)
	{
		std::this_thread::sleep_for(std::chrono::milliseconds(10));
		updateStatus();
	}
}

void GrinderMotionGui::monitorState()
{
	std::this_thread::sleep_for(std::chrono::milliseconds(1000));

	std::cout << "Monitoring state\n";
	while (grinder_should_monitor)
	{
		monitorStateImpl();
		std::this_thread::sleep_for(std::chrono::milliseconds(5));
		mainSequence();
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	}
}

void GrinderMotionGui::monitorStateImpl()
{
	auto updated = updateStatus();
	if (updated < 0)
	{
		std::cerr << "Error updating status\n";
		std::this_thread::sleep_for(std::chrono::milliseconds(1000));
		return;
	}

	updated = updateError();
	if (updated < 0)
	{
		std::cerr << "Error updating error\n";
		std::this_thread::sleep_for(std::chrono::milliseconds(1000));
		return;
	}

	updateStatus();

	bool was_ok = machine_ok.load();
	if (myEmcStatus == nullptr)
	{
		std::cerr << "EMC status is null! LinuxCNC is probably not fully up yet, retrying!\n";
		return;
	}

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
}

void GrinderMotionGui::moveInsideLimits()
{
	// Check X axis limits
	if (current_pos[0] > grinder_settings.x_max && grinder_settings.enable_x)
	{
		std::cout << "X position is greater than max, moving to x_max\n";
		std::stringstream ss;
		ss << "G1 X" << grinder_settings.x_min << " F" << grinder_settings.x_speed;
		sendMDICommand(ss.str().c_str());
	}
	if (current_pos[0] < grinder_settings.x_min && grinder_settings.enable_x)
	{
		std::cout << "X position is less than min, moving to x_min\n";
		std::stringstream ss;
		ss << "G1 X" << grinder_settings.x_max << " F" << grinder_settings.x_speed;
		sendMDICommand(ss.str().c_str());
	}

	// Check Y axis limits
	if (current_pos[1] > grinder_settings.y_max && grinder_settings.enable_y)
	{
		std::cout << "Y position is greater than max, moving to y_max\n";
		std::stringstream ss;
		ss << "G1 Y" << grinder_settings.y_min << " F" << grinder_settings.y_speed;
		sendMDICommand(ss.str().c_str());
	}
	if (current_pos[1] < grinder_settings.y_min && grinder_settings.enable_y)
	{
		std::cout << "Y position is less than min, moving to y_min\n";
		std::stringstream ss;
		ss << "G1 Y" << grinder_settings.y_max << " F" << grinder_settings.y_speed;
		sendMDICommand(ss.str().c_str());
	}

	// Check Z axis limits
	if (current_pos[2] > grinder_settings.z_max && grinder_settings.enable_z)
	{
		std::cout << "Z position is greater than max, moving to z_max\n";
		std::stringstream ss;
		ss << "G1 Z" << grinder_settings.z_min << " F" << grinder_settings.z_speed;
		sendMDICommand(ss.str().c_str());
	}
	if (current_pos[2] < grinder_settings.z_min && grinder_settings.enable_z)
	{
		std::cout << "Z position is less than min, moving to z_min\n";
		std::stringstream ss;
		ss << "G1 Z" << grinder_settings.z_max << " F" << grinder_settings.z_speed;
		sendMDICommand(ss.str().c_str());
	}

	waitForMotionComplete();
}

void GrinderMotionGui::downfeed()
{
	std::cout << "Downfeed\n";
	std::stringstream ss;
	// Get current Y position
	double y_pos = current_pos[2];
	// double y_max = grinder_settings.y_max;
	double y_min = grinder_settings.y_min;
	double y_downfeed_val = grinder_settings.y_downfeed;
	double new_y_pos = y_pos - y_downfeed_val;
	if (new_y_pos < y_min)
	{
		grinder_settings.y_min = new_y_pos;
	}
	ss << "G1 Z" << grinder_settings.z_min << " F" << grinder_settings.z_speed;
	sendMDICommand(ss.str().c_str());
	waitForMotionComplete();
	downfeed_now = false;
}

void GrinderMotionGui::start()
{
	std::cout << "Starting grinder\n";
	if (!is_running && canStart())
	{
		std::cout << "Starting grinder thread\n";
		is_running = true;
		// Emit signal to update GUI
		emit grinderStarted();
	}
	else
	{
		std::cout << "Grinder cannot start, check estop and power\n";
		is_running = false;
		emit grinderStopped();
	}
}

void GrinderMotionGui::stop()
{
	if (is_running)
	{
		is_running = false;
		emit grinderStopped();
	}
}

void GrinderMotionGui::mainSequence()
{
	if (!machine_ok.load())
	{
		std::cout << "Machine not ok\n";
		std::this_thread::sleep_for(std::chrono::milliseconds(500));
		return;
	}

	if (downfeed_now)
	{
		std::cout << "Downfeed now\n";
		if (!is_running)
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

	if (!is_running || !machine_ok.load())
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

	// Update is_running based on external changes
	if (!is_running)
	{
		stop();
		return;
	}

	std::cout << "o<xmove_to_max> call\n";
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

	if (!is_running)
	{
		stop();
	}
}

// GUI-specific method implementations
std::array<double, 3> GrinderMotionGui::getCurrentPosition() const
{
	return {current_pos[0], current_pos[1], current_pos[2]};
}

bool GrinderMotionGui::getMachineOk() const
{
	return machine_ok.load();
}

bool GrinderMotionGui::getIsRunning() const
{
	return is_running;
}

void GrinderMotionGui::jogAxis(int axis, double velocity)
{
	if (!canStart())
	{
		std::cerr << "Cannot jog: machine not ready\n";
		return;
	}

	sendJogCont(axis, JOGTELEOP, velocity);
	std::cout << "Jogging axis " << axis << " at velocity " << velocity << std::endl;
}

void GrinderMotionGui::stopJog()
{
	for (int axis = 0; axis < 3; ++axis)
	{
		sendJogStop(axis, JOGTELEOP);
	}
	std::cout << "Stopping jog" << std::endl;
}

void GrinderMotionGui::setSpindleSpeed(int rpm)
{
	sendSpindleConstant(rpm);
	std::cout << "Setting spindle speed to " << rpm << " RPM" << std::endl;
}

void GrinderMotionGui::setSpindleDirection(bool forward)
{
	if (forward)
	{
		sendSpindleForward(0); // Use spindle 0 (main spindle)
	}
	else
	{
		sendSpindleReverse(0); // Use spindle 0 (main spindle)
	}
	std::cout << "Setting spindle direction: " << (forward ? "forward" : "reverse") << std::endl;
}

void GrinderMotionGui::stopSpindle()
{
	sendSpindleOff(0); // Use spindle 0 (main spindle)
	std::cout << "Stopping spindle" << std::endl;
}

void GrinderMotionGui::setFeedOverride(double percentage)
{
	sendFeedOverride(percentage / 100.0);
	std::cout << "Setting feed override to " << percentage << "%" << std::endl;
}

void GrinderMotionGui::setSpindleOverride(double percentage)
{
	sendSpindleOverride(0, percentage / 100.0); // Use spindle 0 (main spindle)
	std::cout << "Setting spindle override to " << percentage << "%" << std::endl;
}

void GrinderMotionGui::setRapidOverride(double percentage)
{
	sendRapidOverride(percentage / 100.0);
	std::cout << "Setting rapid override to " << percentage << "%" << std::endl;
}

void GrinderMotionGui::runGcodeFile(const std::string &filename)
{
	// Cast away const for the API that expects char*
	sendProgramOpen(const_cast<char *>(filename.c_str()));
	sendProgramRun(0);
	std::cout << "Running G-code file: " << filename << std::endl;
}

void GrinderMotionGui::pauseProgram()
{
	sendProgramPause();
	std::cout << "Pausing program" << std::endl;
}

void GrinderMotionGui::stopProgram()
{
	sendAbort();
	std::cout << "Stopping program" << std::endl;
}

void GrinderMotionGui::homeAxis(int axis)
{
	EMC_JOINT_HOME jointHome;
	jointHome.serial_number = ++command_serial_number;
	jointHome.joint = axis; // Assuming joint corresponds to axis
	sendCommand(jointHome);
	std::cout << "Homing axis " << axis << std::endl;
}

void GrinderMotionGui::homeAllAxes()
{
	for (int axis = 0; axis < 3; ++axis)
	{
		homeAxis(axis);
	}
	std::cout << "Homing all axes" << std::endl;
}

void GrinderMotionGui::touchoffAxis(int axis, double value)
{
	std::stringstream ss;
	char axis_letter = 'X' + axis; // X=0, Y=1, Z=2
	ss << "G10 L20 P0 " << axis_letter << value;
	sendMDICommand(ss.str().c_str());
	std::cout << "Touch off axis " << axis << " to " << value << std::endl;
}

// Grinder-specific operations
void GrinderMotionGui::startGrindingCycle()
{
	start();
}

void GrinderMotionGui::stopGrindingCycle()
{
	stop();
}

void GrinderMotionGui::performDownfeed()
{
	downfeed_now = true;
}

void GrinderMotionGui::updateSettings(const GrinderSettings &settings)
{
	grinder_settings = settings;
	saveSettings();
	emit settingsChanged();
}

GrinderSettings GrinderMotionGui::getSettings() const
{
	return grinder_settings;
}

void GrinderMotionGui::cleanup()
{
	grinder_should_monitor = false;
	if (monitor_thread.joinable())
	{
		monitor_thread.join();
	}

	// Clean up NML connections
	if (command_channel)
	{
		delete command_channel;
		command_channel = nullptr;
	}
	if (error_channel)
	{
		delete error_channel;
		error_channel = nullptr;
	}
}
