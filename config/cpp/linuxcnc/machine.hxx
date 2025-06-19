#pragma once

// #include <QObject>
#include "hal.hxx"
#include <thread>

#include "../settings.hxx"

class Machine /*: public QObject*/
{
	// QObject;

public:
	Machine(Settings &settings);
	~Machine();

	// signals:
	// void PinChanged("")
private:
	void Monitor();

	Hal hal;
	std::thread thread;
};