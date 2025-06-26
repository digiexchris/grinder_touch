#include "machine.hxx"
#include "../pins.hxx"

#include "shcom.hh"
#include <iostream>

Machine::Machine(std::shared_ptr<Settings> aSettings) // thread(&Machine::Monitor, this)
{
	Settings *settings = aSettings.get();

	hal.SetPin(Pin::ZDirection, true);
	hal.SetPin(Pin::DownfeedNow, false);
	hal.SetPin(Pin::IsRunning, false);

	// Setting to the defaults. Expect that the settings aren't loaded yet.
	hal.SetPin(Pin::XMin, 0.0);
	hal.SetPin(Pin::XMax, 0.0);
	hal.SetPin(Pin::YMin, 0.0);
	hal.SetPin(Pin::YMax, 0.0);
	hal.SetPin(Pin::ZMin, 0.0);
	hal.SetPin(Pin::ZMax, 0.0);
	hal.SetPin(Pin::XSpeed, 0.0);
	hal.SetPin(Pin::YSpeed, 0.0);
	hal.SetPin(Pin::ZSpeed, 0.0);
	hal.SetPin(Pin::ZCrossfeed, 0.0);
	hal.SetPin(Pin::YDownfeed, 0.0);
	hal.SetPin(Pin::EnableX, 0.0);
	hal.SetPin(Pin::EnableY, 0.0);
	hal.SetPin(Pin::EnableZ, 0.0);
	hal.SetPin(Pin::StopAtZLimit, 0.0);
	hal.SetPin(Pin::CrossfeedAt, 0.0);
	hal.SetPin(Pin::RepeatAt, 0.0);

	connect(settings, &Settings::AnyPropertyChanged, this, &Machine::SetOnSignal);
}

Machine::~Machine()
{
	if (thread.joinable())
	{
		thread.join();
	}
}

void Machine::SetOnSignal(Pin aPin, std::variant<bool, double, std::string, uint32_t> aValue)
{
	std::cout << "SetOnSignal called for pin: " << static_cast<int>(aPin) << std::endl;

	if (std::holds_alternative<bool>(aValue))
	{
		bool newValue = std::get<bool>(aValue);
		bool oldValue = std::get<bool>(hal.GetPin(aPin));
		if (oldValue == newValue)
		{
			return; // Prevents the loop if the pin is set from a signal that this function caused
		}
		hal.SetPin(aPin, newValue);
	}
	else if (std::holds_alternative<double>(aValue))
	{
		double newValue = std::get<double>(aValue);
		double oldValue = std::get<double>(hal.GetPin(aPin));
		if (oldValue == newValue)
		{
			return;
		}
		hal.SetPin(aPin, newValue);
	}
	else if (std::holds_alternative<std::string>(aValue))
	{
		std::string newValue = std::get<std::string>(aValue);
		std::string oldValue = std::get<std::string>(hal.GetPin(aPin));
		if (oldValue == newValue)
		{
			return;
		}
		hal.SetPin(aPin, newValue);
	}
	else if (std::holds_alternative<uint32_t>(aValue))
	{
		uint32_t newValue = std::get<uint32_t>(aValue);
		uint32_t oldValue = std::get<uint32_t>(hal.GetPin(aPin));
		if (oldValue == newValue)
		{
			return;
		}
		hal.SetPin(aPin, newValue);
	}
	else
	{
		throw std::runtime_error("Unsupported pin value type");
	}
}

void Machine::Monitor()
{

	/*
	loop:

	if(X_MIN pin has changed) {
	  Settings::SetXMin(hal.GetPin(Pin::X_MIN));
 }
	*/

	while (42)
	{
		if (updateStatus() > 0)
		{

			double x = emcStatus->motion.traj.actualPosition.tran.x;
			double y = emcStatus->motion.traj.actualPosition.tran.y;
			double z = emcStatus->motion.traj.actualPosition.tran.z;

			bool positionChangedSinceLast = false;

			if (myPosition.x != x)
			{
				myPosition.x = x;
				positionChangedSinceLast = true;
			}

			if (myPosition.y != y)
			{
				myPosition.y = y;
				positionChangedSinceLast = true;
			}

			if (myPosition.z != z)
			{
				myPosition.z = z;
				positionChangedSinceLast = true;
			}

			if (positionChangedSinceLast)
			{
				emit positionChanged(myPosition);
			}
		}

		std::this_thread::sleep_for(std::chrono::milliseconds(100)); // Adjust the sleep duration as needed
	}
}
