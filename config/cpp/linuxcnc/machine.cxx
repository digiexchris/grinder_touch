#include "machine.hxx"
#include "../pins.hxx"

#include "shcom.hh"
#include "status.hxx"
#include <iostream>

#include <emc_nml.hh>
#include <linuxcnc.h>

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
	stop();
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
	myEstopState = (emcStatus->task.state == EMC_TASK_STATE::ESTOP);
	return myEstopState;
}

void Machine::homeAll()
{
	sendHome(0);
	sendHome(1);
	sendHome(2);
}

void Machine::setPower(bool isOn)
{
	if (isOn)
	{
		sendMachineOn();
	}
	else
	{
		sendMachineOff();
	}
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
	myShouldMonitor = true;
	monitorThread = std::thread(&Monitor, this);
}

void Machine::stop()
{
	myShouldMonitor = false;
	if (monitorThread.joinable())
	{
		monitorThread.join();
	}
}

void Machine::Monitor(Machine *aMachine)
{

	bool isFirstStart = true;

	while (aMachine->myShouldMonitor)
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

			if (positionChangedSinceLast || isFirstStart)
			{
				// Use QMetaObject::invokeMethod for thread-safe signal emission
				QMetaObject::invokeMethod(aMachine, "positionChanged",
										  Qt::QueuedConnection, Q_ARG(Position, aMachine->myPosition));
			}

			{
				EMC_TASK_STATE taskState = emcStatus->task.state;

				bool newEstopState = false;
				bool newPowerState = false;

				switch (taskState)
				{
				case EMC_TASK_STATE::ON:
					newEstopState = false;
					newPowerState = true;
					break;
				case EMC_TASK_STATE::ESTOP:
					newEstopState = true;
					newPowerState = false;
					break;
				case EMC_TASK_STATE::OFF:
					newEstopState = false;
					newPowerState = false;
					break;
				case EMC_TASK_STATE::ESTOP_RESET:
					newEstopState = false;
					newPowerState = false;
					break;
				}

				if (aMachine->myEstopState != newEstopState || isFirstStart)
				{
					aMachine->myEstopState = newEstopState;
					QMetaObject::invokeMethod(aMachine, "estopChanged",
											  Qt::QueuedConnection, Q_ARG(bool, aMachine->myEstopState));
				}

				if (aMachine->myPowerState != newPowerState || isFirstStart)
				{
					aMachine->myPowerState = newPowerState;
					QMetaObject::invokeMethod(aMachine, "powerChanged",
											  Qt::QueuedConnection, Q_ARG(bool, aMachine->myPowerState));
				}
			}

			if ((
					aMachine->myIsHomed[0] != (emcStatus->motion.joint[0].homed != 0) ||
					aMachine->myIsHomed[1] != (emcStatus->motion.joint[1].homed != 0) ||
					aMachine->myIsHomed[2] != (emcStatus->motion.joint[2].homed != 0)) ||
				isFirstStart)
			{
				aMachine->myIsHomed[0] = (emcStatus->motion.joint[0].homed != 0);
				aMachine->myIsHomed[1] = (emcStatus->motion.joint[1].homed != 0);
				aMachine->myIsHomed[2] = (emcStatus->motion.joint[2].homed != 0);
			}

			bool homed = aMachine->myIsHomed[0] && aMachine->myIsHomed[1] && aMachine->myIsHomed[2];
			if (aMachine->myAllHomed != homed || isFirstStart)
			{
				aMachine->myAllHomed = homed;
				QMetaObject::invokeMethod(aMachine, "homeChanged",
										  Qt::QueuedConnection, Q_ARG(bool, aMachine->myAllHomed));
			}
			if (isFirstStart)
			{
				isFirstStart = false;
			}
		}
		std::this_thread::sleep_for(std::chrono::milliseconds(100));
	}
}
