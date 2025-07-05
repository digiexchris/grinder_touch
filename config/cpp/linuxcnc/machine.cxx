#include "machine.hxx"
#include "../pins.hxx"

#include "shcom.hh"
#include <iostream>

Machine::Machine(std::shared_ptr<Settings> aSettings) // thread(&Machine::Monitor, this)
{
	Settings *settings = aSettings.get();
	connect(settings, &Settings::AnyPropertyChanged, this, &Machine::SetOnSignal);

	if (updateStatus() < 0)
	{
		throw std::runtime_error("Failed to update machine status");
	}

	if (emcTaskNmlGet() < 0)
	{
		throw std::runtime_error("Failed to get EMC task NML");
	}
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
		// todo for some reason the bool type doesn't work with HAL_BIT
		//  bool newValue = std::get<bool>(aValue);
		//  std::variant<bool, double, std::string, uint32_t> oldRawValue = hal.GetPin(aPin);
		//  bool oldValue = std::get<bool>(oldRawValue);
		//  if (oldValue == newValue)
		//  {
		//  	return; // Prevents the loop if the pin is set from a signal that this function caused
		//  }
		//  hal.SetPin(aPin, newValue);
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

bool Machine::isEstopActive()
{
	eStopState = (emcStatus->task.state == EMC_TASK_STATE::ESTOP);
	return eStopState;
}

void Machine::setEstop(bool isActive)
{
	if (isActive)
	{
		sendEstop();
	}
	else
	{
		sendEstopReset();
	}
}

void Machine::start()
{
	monitorThread = std::thread(&Monitor, this);
}

void Machine::Monitor(Machine *aMachine)
{

	while (42)
	{
		if (updateStatus() > 0)
		{

			double x = emcStatus->motion.traj.actualPosition.tran.x;
			double y = emcStatus->motion.traj.actualPosition.tran.y;
			double z = emcStatus->motion.traj.actualPosition.tran.z;

			bool positionChangedSinceLast = false;

			if (aMachine->myPosition.x != x)
			{
				aMachine->myPosition.x = x;
				positionChangedSinceLast = true;
			}

			if (aMachine->myPosition.y != y)
			{
				aMachine->myPosition.y = y;
				positionChangedSinceLast = true;
			}

			if (aMachine->myPosition.z != z)
			{
				aMachine->myPosition.z = z;
				positionChangedSinceLast = true;
			}

			if (positionChangedSinceLast)
			{
				emit aMachine->positionChanged(aMachine->myPosition);
			}

			if (aMachine->eStopState != (emcStatus->task.state == EMC_TASK_STATE::ESTOP))
			{
				aMachine->eStopState = (emcStatus->task.state == EMC_TASK_STATE::ESTOP);
				emit aMachine->estopChanged(aMachine->eStopState);
			}
		}

		std::this_thread::sleep_for(std::chrono::milliseconds(100)); // Adjust the sleep duration as needed
	}
}
