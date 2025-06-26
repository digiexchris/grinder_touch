// #include "grinder_motion.hxx"
// #include "gui_events.hxx"
// #include "linuxcnc/emc.hh"
// #include "linuxcnc/nml.hh"
// #include "linuxcnc/rcs.hh"
// #include "linuxcnc/stat_msg.hh"
// #include "nmlmsg.hh"
// // #include "shcom.hh"
// #include <cassert>
// #include <csignal>
// #include <cstdlib>
// #include <cstring>
// #include <iostream>
// #include <sstream>

// // #include "grinder_gui.hxx"

// #ifndef EMC2_DEFAULT_INIFILE
// #define EMC2_DEFAULT_INIFILE "/usr/share/linuxcnc/linuxcnc.ini"
// #endif

// #define UNUSED(x) (void)(x)

// GrinderMotion::GrinderMotion(SettingsManager *aSettingsManager, bool standaloneMode)
// 	: isStandalone(standaloneMode), is_running(false), grinder_should_monitor(true),
// 	  is_first_run(true), downfeed_now(false), mySettingsManager(aSettingsManager)
// {
// 	is_running.store(false);

// 	if (aSettingsManager == nullptr)
// 	{
// 		std::cerr << "SettingsManager is null!\n";
// 		throw std::runtime_error("SettingsManager cannot be null");
// 	}
// }

// GrinderMotion::~GrinderMotion()
// {
// 	cleanup();
// }

// void GrinderMotion::Start()
// {
// 	if (isStandalone)
// 	{
// 		std::cout << "Standalone mode: Skipping LinuxCNC backend initialization\n";
// 		return;
// 	}

// 	// Initialize LinuxCNC NML connections without HAL
// 	for (int i = 0; i < 10; ++i)
// 	{
// 		updateStatus();
// 		myEmcStatus = emcStatusGet();
// 		if (myEmcStatus == nullptr)
// 		{
// 			std::cerr << "EMC status is null! LinuxCNC is probably not fully up yet, retrying!\n";
// 			std::this_thread::sleep_for(std::chrono::milliseconds(500));
// 			continue;
// 		}
// 		else
// 		{
// 			std::cout << "EMC is online!\n";
// 			break;
// 		}
// 	}

// 	// Initialize NML
// 	initializeNML();

// 	// start the monitor thread

// 	monitor_thread = std::thread(&GrinderMotion::monitorState, this);
// 	std::cout << "Grinder motion started\n";
// }

// void GrinderMotion::initializeNML()
// {
// 	assert(tryNml(10, 2) >= 0);
// 	updateStatus();
// 	std::cout << "EMC status address: " << myEmcStatus << '\n';

// 	// Set initial mode to manual
// 	setMDIMode();
// }

// bool GrinderMotion::checkErrors()
// {
// 	// Wait for previous commands to complete and check for errors
// 	while (error_channel->get_queue_length() > 0)
// 	{
// 		NMLTYPE type = error_channel->read();
// 		if (type != 0)
// 		{
// 			std::cerr << "Error executing command: " << type << '\n';
// 			return false;
// 		}
// 	}
// 	return true;
// }

// bool GrinderMotion::sendCommand(NMLmsg &msg)
// {
// 	if (command_channel->write(msg) != 0)
// 	{
// 		std::cerr << "Failed to send command\n";
// 		return false;
// 	}
// 	return checkErrors();
// }

// bool GrinderMotion::setMDIMode()
// {
// 	if (isStandalone)
// 	{
// 		std::cerr << "Cannot send MDI command in standalone mode\n";
// 		return true;
// 	}
// 	sendMdi();
// 	return true;
// }

// void GrinderMotion::sendMDICommand(const char *command)
// {
// 	if (isStandalone)
// 	{
// 		std::cerr << "Cannot send MDI command in standalone mode\n";
// 		return;
// 	}

// 	if (!command)
// 	{
// 		std::cerr << "Command is null!\n";
// 		return;
// 	}

// 	std::cout << "Sending MDI command: " << command << std::endl;

// 	EMC_TASK_PLAN_EXECUTE taskPlanExecute;
// 	strcpy(taskPlanExecute.command, command);
// 	sendCommand(taskPlanExecute);
// }

// bool GrinderMotion::canStart()
// {
// 	if (isStandalone)
// 	{
// 		std::cerr << "Standalone mode set, pretending it can start\n";
// 		return true;
// 	}

// 	if (myEmcStatus == nullptr)
// 	{
// 		return false;
// 	}

// 	return !(myEmcStatus->task.state == EMC_TASK_STATE_ESTOP) &&
// 		   myEmcStatus->task.state == EMC_TASK_STATE_ON &&
// 		   myEmcStatus->motion.traj.enabled;
// }

// void GrinderMotion::waitForMotionComplete()
// {
// 	if (isStandalone)
// 	{
// 		return;
// 	}

// 	if (myEmcStatus == nullptr)
// 	{
// 		return;
// 	}

// 	while (myEmcStatus->motion.traj.queue > 0)
// 	{
// 		std::this_thread::sleep_for(std::chrono::milliseconds(10));
// 		updateStatus();
// 	}
// }

// void GrinderMotion::monitorState()
// {
// 	std::this_thread::sleep_for(std::chrono::milliseconds(1000));

// 	std::cout << "Monitoring state\n";
// 	while (grinder_should_monitor)
// 	{
// 		updateState();

// 		bool is_ok = retrievedStatus.isEstopActive == false &&
// 					 retrievedStatus.isPowerOn == true &&
// 					 retrievedStatus.isHomed == true;
// 		if (is_ok)
// 		{
// 			mainSequence();
// 			std::this_thread::sleep_for(std::chrono::milliseconds(10));
// 		}
// 		else
// 		{
// 			std::this_thread::sleep_for(std::chrono::milliseconds(50));
// 		}
// 	}
// }

// void GrinderMotion::moveInsideLimits()
// {
// 	// Check X axis limits
// 	if (current_pos[0] > grinder_settings.x_max && grinder_settings.enable_x)
// 	{
// 		std::cout << "X position is greater than max, moving to x_max\n";
// 		std::stringstream ss;
// 		ss << "G1 X" << grinder_settings.x_min << " F" << grinder_settings.x_speed;
// 		sendMDICommand(ss.str().c_str());
// 	}
// 	if (current_pos[0] < grinder_settings.x_min && grinder_settings.enable_x)
// 	{
// 		std::cout << "X position is less than min, moving to x_min\n";
// 		std::stringstream ss;
// 		ss << "G1 X" << grinder_settings.x_max << " F" << grinder_settings.x_speed;
// 		sendMDICommand(ss.str().c_str());
// 	}

// 	// Check Y axis limits
// 	if (current_pos[1] > grinder_settings.y_max && grinder_settings.enable_y)
// 	{
// 		std::cout << "Y position is greater than max, moving to y_max\n";
// 		std::stringstream ss;
// 		ss << "G1 Y" << grinder_settings.y_min << " F" << grinder_settings.y_speed;
// 		sendMDICommand(ss.str().c_str());
// 	}
// 	if (current_pos[1] < grinder_settings.y_min && grinder_settings.enable_y)
// 	{
// 		std::cout << "Y position is less than min, moving to y_min\n";
// 		std::stringstream ss;
// 		ss << "G1 Y" << grinder_settings.y_max << " F" << grinder_settings.y_speed;
// 		sendMDICommand(ss.str().c_str());
// 	}

// 	// Check Z axis limits
// 	if (current_pos[2] > grinder_settings.z_max && grinder_settings.enable_z)
// 	{
// 		std::cout << "Z position is greater than max, moving to z_max\n";
// 		std::stringstream ss;
// 		ss << "G1 Z" << grinder_settings.z_min << " F" << grinder_settings.z_speed;
// 		sendMDICommand(ss.str().c_str());
// 	}
// 	if (current_pos[2] < grinder_settings.z_min && grinder_settings.enable_z)
// 	{
// 		std::cout << "Z position is less than min, moving to z_min\n";
// 		std::stringstream ss;
// 		ss << "G1 Z" << grinder_settings.z_max << " F" << grinder_settings.z_speed;
// 		sendMDICommand(ss.str().c_str());
// 	}

// 	waitForMotionComplete();
// }

// void GrinderMotion::downfeed()
// {
// 	std::cout << "Downfeed\n";
// 	std::stringstream ss;
// 	// Get current Y position
// 	double y_pos = current_pos[2];
// 	// double y_max = grinder_settings.y_max;
// 	double y_min = grinder_settings.y_min;
// 	double y_downfeed_val = grinder_settings.y_downfeed;
// 	double new_y_pos = y_pos - y_downfeed_val;
// 	if (new_y_pos < y_min)
// 	{
// 		grinder_settings.y_min = new_y_pos;
// 	}
// 	ss << "G1 Z" << grinder_settings.z_min << " F" << grinder_settings.z_speed;
// 	sendMDICommand(ss.str().c_str());
// 	waitForMotionComplete();
// 	downfeed_now = false;
// }

// void GrinderMotion::onJog(Axis axis, bool direction)
// {
// 	int axisNum = static_cast<int>(axis);
// 	if (!canStart())
// 	{
// 		std::cerr << "Cannot jog: machine not ready\n";
// 		return;
// 	}

// 	if (axisNum < 0 || axisNum >= 3)
// 	{
// 		std::cerr << "Invalid axis: " << axisNum << std::endl;
// 		return;
// 	}

// 	// todo figure out if step or continuous mode is set and send the correct type via shcomm: sendJogCont or sendJogIncr
// 	// todo get velocity from UI, jog velocity is not a linuxcnc status variable

// 	// auto velocity = emcStatus->motion.traj.velocity

// 	int velocity = 100;

// 	sendJogCont(axisNum, JOGTELEOP, velocity);
// 	std::cout << "Jogging axis " << axisNum << " at velocity " << velocity << std::endl;
// }

// void GrinderMotion::onJogStop(Axis axis)
// {
// 	sendJogStop(static_cast<int>(axis), JOGTELEOP);
// 	std::cout << "Stopping jog for axis " << static_cast<int>(axis) << "\n";
// }

// void GrinderMotion::start()
// {
// 	std::cout << "Starting grinder\n";
// 	if (!is_running && canStart())
// 	{
// 		std::cout << "Starting grinder thread\n";
// 		is_running = true;
// 		// Emit signal to update GUI
// 		emit grinderStarted();
// 	}
// 	else
// 	{
// 		emit errorMessage(
// 			tr("Grinder cannot start, check estop and power"));
// 		is_running = false;
// 		emit grinderStopped();
// 	}
// }

// void GrinderMotion::stop()
// {
// 	if (is_running)
// 	{
// 		is_running = false;
// 		emit grinderStopped();
// 	}
// }

// bool GrinderMotion::isOk()
// {
// 	if (isStandalone)
// 	{
// 		std::cout << "Standalone mode: isOk always returns true\n";
// 		return true;
// 	}

// 	if (myEmcStatus == nullptr)
// 	{
// 		std::cerr << "EMC status is null!\n";
// 		return false;
// 	}

// 	return retrievedStatus.isEstopActive == false &&
// 		   retrievedStatus.isPowerOn == true &&
// 		   retrievedStatus.isHomed == true;
// }

// void GrinderMotion::mainSequence()
// {
// 	if (downfeed_now)
// 	{
// 		std::cout << "Downfeed now\n";
// 		if (!is_running)
// 		{
// 			if (!setMDIMode())
// 			{
// 				std::cerr << "Failed to set MDI mode\n";
// 				stop();
// 				return;
// 			}
// 			waitForMotionComplete();
// 		}
// 		downfeed();
// 	}

// 	updateStatus();
// 	if (!is_running || !isOk())
// 	{
// 		return;
// 	}

// 	if (is_first_run)
// 	{
// 		is_first_run = false;
// 		std::cout << "Ensuring MDI mode is set\n";
// 		if (!setMDIMode())
// 		{
// 			std::cerr << "Failed to set MDI mode\n";
// 			stop();
// 			return;
// 		}
// 		waitForMotionComplete();
// 	}

// 	updateStatus();
// 	if (!is_running || !isOk())
// 	{
// 		stop();
// 		return;
// 	}

// 	std::cout << "o<xmove_to_max> call\n";
// 	sendMDICommand("o<xmove_to_max> call");
// 	waitForMotionComplete();

// 	updateStatus();
// 	if (!is_running || !isOk())
// 	{
// 		stop();
// 		return;
// 	}

// 	std::cout << "o<xmove_to_min> call\n";
// 	sendMDICommand("o<xmove_to_min> call");
// 	waitForMotionComplete();

// 	updateStatus();
// 	if (!is_running || !isOk())
// 	{
// 		stop();
// 		return;
// 	}
// }

// // GUI-specific method implementations
// Position GrinderMotion::getCurrentPosition() const
// {
// 	return {current_pos[0], current_pos[1], current_pos[2]};
// }

// bool GrinderMotion::getIsRunning() const
// {
// 	return is_running;
// }

// // void GrinderMotion::jogAxis(int axis, double velocity)
// // {
// // 	if (!canStart())
// // 	{
// // 		std::cerr << "Cannot jog: machine not ready\n";
// // 		return;
// // 	}

// // 	sendJogCont(axis, JOGTELEOP, velocity);
// // 	std::cout << "Jogging axis " << axis << " at velocity " << velocity << std::endl;
// // }

// // void GrinderMotion::stopJog()
// // {
// // 	for (int axis = 0; axis < 3; ++axis)
// // 	{
// // 		sendJogStop(axis, JOGTELEOP);
// // 	}
// // 	std::cout << "Stopping jog" << std::endl;
// // }

// // void GrinderMotion::setSpindleSpeed(int rpm)
// // {
// // 	sendSpindleConstant(rpm);
// // 	std::cout << "Setting spindle speed to " << rpm << " RPM" << std::endl;
// // }

// // void GrinderMotion::setSpindleDirection(bool forward)
// // {
// // 	if (forward)
// // 	{
// // 		sendSpindleForward(0); // Use spindle 0 (main spindle)
// // 	}
// // 	else
// // 	{
// // 		sendSpindleReverse(0); // Use spindle 0 (main spindle)
// // 	}
// // 	std::cout << "Setting spindle direction: " << (forward ? "forward" : "reverse") << std::endl;
// // }

// // void GrinderMotion::stopSpindle()
// // {
// // 	sendSpindleOff(0); // Use spindle 0 (main spindle)
// // 	std::cout << "Stopping spindle" << std::endl;
// // }

// // void GrinderMotion::setFeedOverride(double percentage)
// // {
// // 	sendFeedOverride(percentage / 100.0);
// // 	std::cout << "Setting feed override to " << percentage << "%" << std::endl;
// // }

// // void GrinderMotion::setSpindleOverride(double percentage)
// // {
// // 	sendSpindleOverride(0, percentage / 100.0); // Use spindle 0 (main spindle)
// // 	std::cout << "Setting spindle override to " << percentage << "%" << std::endl;
// // }

// // void GrinderMotion::setRapidOverride(double percentage)
// // {
// // 	sendRapidOverride(percentage / 100.0);
// // 	std::cout << "Setting rapid override to " << percentage << "%" << std::endl;
// // }

// // void GrinderMotion::runGcodeFile(const std::string &filename)
// // {
// // 	// Cast away const for the API that expects char*
// // 	sendProgramOpen(const_cast<char *>(filename.c_str()));
// // 	sendProgramRun(0);
// // 	std::cout << "Running G-code file: " << filename << std::endl;
// // }

// // void GrinderMotion::pauseProgram()
// // {
// // 	sendProgramPause();
// // 	std::cout << "Pausing program" << std::endl;
// // }

// // void GrinderMotion::stopProgram()
// // {
// // 	sendAbort();
// // 	std::cout << "Stopping program" << std::endl;
// // }

// void GrinderMotion::homeAxis(int axis)
// {
// 	EMC_JOINT_HOME jointHome;
// 	jointHome.serial_number = ++command_serial_number;
// 	jointHome.joint = axis; // Assuming joint corresponds to axis
// 	sendCommand(jointHome);
// 	std::cout << "Homing axis " << axis << std::endl;
// }

// void GrinderMotion::onHomeAll()
// {
// 	for (int axis = 0; axis < 3; ++axis)
// 	{
// 		homeAxis(axis);
// 	}
// 	std::cout << "Homing all axes" << std::endl;
// }

// // void GrinderMotion::touchoffAxis(int axis, double value)
// // {
// // 	std::stringstream ss;
// // 	char axis_letter = 'X' + axis; // X=0, Y=1, Z=2
// // 	ss << "G10 L20 P0 " << axis_letter << value;
// // 	sendMDICommand(ss.str().c_str());
// // 	std::cout << "Touch off axis " << axis << " to " << value << std::endl;
// // }

// // Grinder-specific operations
// void GrinderMotion::startGrindingCycle()
// {
// 	start();
// }

// void GrinderMotion::stopGrindingCycle()
// {
// 	stop();
// }

// void GrinderMotion::performDownfeed()
// {
// 	downfeed_now = true;
// }
// void GrinderMotion::cleanup()
// {
// 	grinder_should_monitor = false;

// 	// Clean up NML connections
// 	// if (command_channel)
// 	// {
// 	// 	delete command_channel;
// 	// 	command_channel = nullptr;
// 	// }
// 	// if (error_channel)
// 	// {
// 	// 	delete error_channel;
// 	// 	error_channel = nullptr;
// 	// }
// }

// void GrinderMotion::updateState()
// {
// 	updateStatus();
// 	if (myEmcStatus == nullptr)
// 	{
// 		std::cerr << "EMC status is null! Cannot update position.\n";
// 		return;
// 	}

// 	if (current_pos[0] != myEmcStatus->motion.traj.position.tran.x ||
// 		current_pos[1] != myEmcStatus->motion.traj.position.tran.y ||
// 		current_pos[2] != myEmcStatus->motion.traj.position.tran.z)
// 	{
// 		current_pos[0] = myEmcStatus->motion.traj.position.tran.x;
// 		current_pos[1] = myEmcStatus->motion.traj.position.tran.y;
// 		current_pos[2] = myEmcStatus->motion.traj.position.tran.z;

// 		emit positionChanged(current_pos[0], current_pos[1], current_pos[2]);
// 	}

// 	if (retrievedStatus.isEstopActive != myEmcStatus->task.state == EMC_TASK_STATE_ESTOP)
// 	{
// 		retrievedStatus.isEstopActive = myEmcStatus->task.state == EMC_TASK_STATE_ESTOP;

// 		if (retrievedStatus.isEstopActive && is_running)
// 		{
// 			std::cout << "Emergency stop activated, stopping grinder\n";
// 			stop();
// 		}
// 		emit estopChanged(retrievedStatus.isEstopActive);
// 	}

// 	if (retrievedStatus.isPowerOn != myEmcStatus->task.state == EMC_TASK_STATE_ON)
// 	{
// 		retrievedStatus.isPowerOn = myEmcStatus->task.state == EMC_TASK_STATE_ON;

// 		if (!retrievedStatus.isPowerOn && is_running)
// 		{
// 			std::cout << "Power turned off, stopping grinder\n";
// 			stop();
// 		}

// 		emit powerChanged(retrievedStatus.isPowerOn);
// 	}

// 	if (retrievedStatus.isHomed != myEmcStatus->motion.traj.enabled)
// 	{
// 		retrievedStatus.isHomed = myEmcStatus->motion.traj.enabled;
// 		emit homedChanged(retrievedStatus.isHomed);
// 	}
// }

// void GrinderMotion::onToggleEstop()
// {
// 	if (retrievedStatus.isEstopActive)
// 	{
// 		std::cout << "Disabling emergency stop\n";
// 		sendEstopReset();
// 	}
// 	else
// 	{
// 		std::cout << "Enabling emergency stop\n";
// 		sendEstop();
// 	}
// }

// void GrinderMotion::onTogglePower()
// {
// 	if (retrievedStatus.isPowerOn)
// 	{
// 		std::cout << "Turning off power\n";
// 		sendMachineOff();
// 	}
// 	else
// 	{
// 		std::cout << "Turning on power\n";
// 		sendMachineOn();
// 	}
// }
