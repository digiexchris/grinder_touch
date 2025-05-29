#pragma once

#include "linuxcnc/emc_nml.hh"
#include "linuxcnc/hal.h"
#include "settings.hxx"
#include <array>
#include <atomic>
#include <thread>

struct GrinderPins
{
	hal_float_t *x_min, *x_max, *y_min, *y_max, *z_min, *z_max;
	hal_float_t *x_speed, *y_speed, *z_speed;
	hal_bit_t *z_direction, *enable_x, *enable_y, *enable_z;
	hal_bit_t *stop_at_z_limit, *is_running;
	hal_float_t *z_crossfeed, *y_downfeed;
	hal_s32_t *crossfeed_at, *repeat_at;
	hal_bit_t *downfeed_now;
	hal_float_t *dress_start_x, *dress_start_y, *dress_start_z;
	hal_float_t *dress_end_x, *dress_end_y, *dress_end_z;
	hal_float_t *dress_stepover_x, *dress_stepover_y, *dress_stepover_z;
	hal_float_t *dress_wheel_rpm;
	hal_float_t *dress_wheel_dia;
	hal_float_t *dress_point_dia;
	hal_s32_t *dress_offset_gcode;
	hal_bit_t *requires_save;
};

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
	int hal_comp_id;
	GrinderPins *grinder_pins;
	bool grinder_should_monitor;
	bool is_first_run = false;
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
