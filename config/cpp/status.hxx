#pragma once

enum class Axis
{
	X = 0,
	Y = 1,
	Z = 2
};

struct Position
{
	double x;
	double y;
	double z;
	Position(double x_val = 0.0, double y_val = 0.0, double z_val = 0.0)
		: x(x_val), y(y_val), z(z_val) {}
};

struct LinuxCncStatus
{
	bool machineOk;
	bool isRunning;
	Position currentPos;
	double spindleSpeed;
	bool spindleForward;
	bool spindleOn;
	int feedOverridePercentage;
	int jogVelocity[3]; // X, Y, Z axis jog velocities
						// int errors;			// Error count or error code
};