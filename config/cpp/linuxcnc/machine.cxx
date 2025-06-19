#include "machine.hxx"

Machine::Machine(Settings &settings) // thread(&Machine::Monitor, this)
{

	hal.SetPin(Pin::Z_DIRECTION, true);
	hal.SetPin(Pin::DOWNFEED_NOW, false);
	hal.SetPin(Pin::IS_RUNNING, false);

	hal.SetPin(Pin::X_MIN, settings.x_min);
	hal.SetPin(Pin::X_MAX, settings.x_max);
	hal.SetPin(Pin::Y_MIN, settings.y_min);
	hal.SetPin(Pin::Y_MAX, settings.y_max);
	hal.SetPin(Pin::Z_MIN, settings.z_min);
	hal.SetPin(Pin::Z_MAX, settings.z_max);
	hal.SetPin(Pin::X_SPEED, settings.x_speed);
	hal.SetPin(Pin::Y_SPEED, settings.y_speed);
	hal.SetPin(Pin::Z_SPEED, settings.z_speed);
	hal.SetPin(Pin::Z_CROSSFEED, settings.z_crossfeed);
	hal.SetPin(Pin::Y_DOWNFEED, settings.y_downfeed);
	hal.SetPin(Pin::ENABLE_X, settings.enable_x);
	hal.SetPin(Pin::ENABLE_Y, settings.enable_y);
	hal.SetPin(Pin::ENABLE_Z, settings.enable_z);
	hal.SetPin(Pin::STOP_AT_Z_LIMIT, settings.stop_at_z_limit);
	hal.SetPin(Pin::CROSSFEED_AT, settings.crossfeed_at);
	hal.SetPin(Pin::REPEAT_AT, settings.repeat_at);
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