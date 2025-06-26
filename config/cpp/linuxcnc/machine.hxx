#pragma once

#include "hal.hxx"
#include <QObject>
#include <thread>

#include "../settings.hxx"
#include "emc_nml.hh"
#include "status.hxx"
#include <linuxcnc/linuxcnc.h>

class Machine : public QObject
{
	Q_OBJECT
public:
	Machine(std::shared_ptr<Settings> settings);
	~Machine();

signals:
	void positionChanged(Position aPosition);

private:
	void Monitor();

	void SetOnSignal(Pin aPin, std::variant<bool, double, std::string, uint32_t> aValue);

	Hal hal;
	std::thread thread;
	int myShmFd = -1; // Shared memory file descriptor
	// linuxcnc_status_t *myStatus = nullptr; // Pointer to the shared memory status structure

	Position myPosition = {0.0, 0.0, 0.0}; // X, Y, Z positions
};