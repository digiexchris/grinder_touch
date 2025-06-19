#pragma once

#include "linuxcnc/emc_nml.hh"
#include "linuxcnc/hal.h"
#include "settings.hxx"
#include <array>
#include <atomic>
#include <thread>

class GrinderMotion
{
private:
	// RCS_STAT_CHANNEL *stat_channel;
	EMC_STAT *myEmcStatus;
	NML *error_channel;
	NML *command_channel;
	std::atomic<bool> is_running;
	std::atomic<bool> machine_ok;
	std::thread main_thread;
	std::thread monitor_thread;
	// int hal_comp_id;
	// GrinderPins *grinder_pins;
	bool grinder_should_monitor;
	bool is_first_run = true;
	std::array<double, 9> current_pos;
	SettingsManager *mySettingsManager;

	void monitorStateImpl();
	void waitForMotionComplete();
	bool checkErrors();
	bool sendCommand(NMLmsg &msg);
	bool setMDIMode();
	void mainSequence();
	void moveInsideLimits();
	void downfeed();
	void save();

public:
	GrinderMotion(SettingsManager *aSettingsManager);
	~GrinderMotion();

	void Start();
	void monitorState();
	void initializeNML();
	void initializeHAL();
	void sendMDICommand(const char *command);
	bool canStart();
	void start();
	void stop();
	[[nodiscard]] bool getIsRunning() const;
	// [[nodiscard]] hal_bit_t getIsRunningPin() const;
	void cleanup();
};
