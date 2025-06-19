#include "machine.hxx"

Machine::Machine(Settings &settings) // thread(&Machine::Monitor, this)
{
	hal.SetPin(Pin::Z_DIRECTION, true);
	// // Initialize default values - note the dereferencing
	// *(pins->z_direction) = true;
	// *(pins->downfeed_now) = false;
	// *(pins->is_running) = false;
	// *(pins->requires_save) = false;

	// auto settings = mySettingsManager->Get();
	// *(pins->x_min) = settings->x_min;
	// *(pins->x_max) = settings->x_max;
	// *(pins->y_min) = settings->y_min;
	// *(pins->y_max) = settings->y_max;
	// *(pins->z_min) = settings->z_min;
	// *(pins->z_max) = settings->z_max;
	// *(pins->x_speed) = settings->x_speed;
	// *(pins->y_speed) = settings->y_speed;
	// *(pins->z_speed) = settings->z_speed;
	// *(pins->z_crossfeed) = settings->z_crossfeed;
	// *(pins->y_downfeed) = settings->y_downfeed;
	// *(pins->enable_x) = settings->enable_x;
	// *(pins->enable_y) = settings->enable_y;
	// *(pins->enable_z) = settings->enable_z;
	// *(pins->stop_at_z_limit) = settings->stop_at_z_limit;
	// *(pins->crossfeed_at) = settings->crossfeed_at;
	// *(pins->repeat_at) = settings->repeat_at;
	// *(pins->dress_start_x) = settings->dress_start_x;
	// *(pins->dress_start_y) = settings->dress_start_y;
	// *(pins->dress_start_z) = settings->dress_start_z;
	// *(pins->dress_end_x) = settings->dress_end_x;
	// *(pins->dress_end_y) = settings->dress_end_y;
	// *(pins->dress_end_z) = settings->dress_end_z;
	// *(pins->dress_stepover_x) = settings->dress_stepover_x;
	// *(pins->dress_stepover_y) = settings->dress_stepover_y;
	// *(pins->dress_stepover_z) = settings->dress_stepover_z;
	// *(pins->dress_wheel_rpm) = settings->dress_wheel_rpm;
	// *(pins->dress_wheel_dia) = settings->dress_wheel_dia;
}

Machine::~Machine()
{
	if (thread.joinable())
	{
		thread.join();
	}
}

void Machine::Monitor()
{
}