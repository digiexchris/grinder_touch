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
	bool isEstopActive = true;
	bool isPowerOn = false;
	bool isHomed = false;
	double spindleSpeed = 0.0;
	bool spindleForward = false;
	bool spindleOn = false;
	int feedOverridePercentage = 100;
};