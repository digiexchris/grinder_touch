#pragma once

#include "hal.hxx"
#include <QObject>
#include <thread>

#include "../settings.hxx"
#include "emc_nml.hh"
#include "shcom.hh"
#include "status.hxx"
#include <linuxcnc/linuxcnc.h>

class Machine : public QObject
{
	Q_OBJECT
public:
	Machine(std::shared_ptr<Settings> settings);
	~Machine();

	void start();
	void stop();

	bool isEstopActive();
	bool isHomed() const { return myAllHomed; }
	bool isOn() const { return myPowerState; }
	void homeAll();
	void setPower(bool isOn);
	void setEstop(bool isActive);

signals:
	void positionChanged(Position aPosition);
	void estopChanged(bool isActive);
	void powerChanged(bool isOn);
	void homeChanged(bool isHomed);

private:
	static void Monitor(Machine *aMachine);

	void SetOnSignal(Pin aPin, std::variant<bool, double, std::string, uint32_t> aValue);

	Hal hal;

	Position myPosition = {0.0, 0.0, 0.0}; // X, Y, Z positions
	bool myEstopState = false;
	bool myIsHomed[3] = {false, false, false}; // X, Y, Z homed states
	bool myAllHomed = false;

	bool myPowerState = false;

	bool myShouldMonitor = true;

	std::thread monitorThread;
};