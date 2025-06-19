#include "hal.hxx"
#include "linuxcnc/hal.h"

#include <variant>

// #include <cassert>
// #include <csignal>
// #include <cstdlib>
// #include <cstring>
// #include <cxxabi.h>
#include <iostream>
#include <stdexcept>
// #include <sstream>

template <typename T>
void Hal::CreatePin(Pin aPin, std::string aName, hal_pin_dir_t aDirection)
{
	pins.try_emplace(aPin, T(aPin, aName, aDirection, componentName, componentId));
}

Hal::Hal()
{ // Use a unique name for loadusr

	// Initialize with number of pins we'll create
	componentId = hal_init(componentName.c_str());

	if (componentId < 0)
	{
		std::cout << "Failed to initialize HAL component" << std::to_string(componentId) << "\n";
		throw std::runtime_error("Failed to initialize HAL component: " + std::to_string(componentId));
	}

	componentIsInitalized = true;

	// Create pins with component prefix
	const std::string prefix = std::string(componentName) + ".";

	CreatePin<HalFloat>(Pin::X_MIN, "x_min", HAL_IN);
	CreatePin<HalFloat>(Pin::X_MAX, "x_max", HAL_IN);
	CreatePin<HalFloat>(Pin::Y_MIN, "y_min", HAL_IN);
	CreatePin<HalFloat>(Pin::Y_MAX, "y_max", HAL_IN);
	CreatePin<HalFloat>(Pin::Z_MIN, "z_min", HAL_IN);
	CreatePin<HalFloat>(Pin::Z_MAX, "z_max", HAL_IN);
	CreatePin<HalFloat>(Pin::X_SPEED, "x_speed", HAL_IN);
	CreatePin<HalFloat>(Pin::Y_SPEED, "y_speed", HAL_IN);
	CreatePin<HalFloat>(Pin::Z_SPEED, "z_speed", HAL_IN);
	CreatePin<HalBit>(Pin::Z_DIRECTION, "z_direction", HAL_IO);
	CreatePin<HalFloat>(Pin::Z_CROSSFEED, "z_crossfeed", HAL_IN);
	CreatePin<HalFloat>(Pin::Y_DOWNFEED, "y_downfeed", HAL_IN);
	CreatePin<HalBit>(Pin::ENABLE_X, "enable_x", HAL_IO);
	CreatePin<HalBit>(Pin::ENABLE_Y, "enable_y", HAL_IO);
	CreatePin<HalBit>(Pin::ENABLE_Z, "enable_z", HAL_IO);
	CreatePin<HalBit>(Pin::STOP_AT_Z_LIMIT, "stop_at_z_limit", HAL_IN);
	CreatePin<HalU32>(Pin::CROSSFEED_AT, "crossfeed_at", HAL_IN);
	CreatePin<HalU32>(Pin::REPEAT_AT, "repeat_at", HAL_IN);
	CreatePin<HalBit>(Pin::IS_RUNNING, "is_running", HAL_IO);
	CreatePin<HalBit>(Pin::DOWNFEED_NOW, "downfeed_now", HAL_IO);

	std::cout << "HAL pins created\n";

	hal_ready(componentId);
}

Hal::~Hal()
{
	if (componentIsInitalized)
	{
		hal_exit(componentId);
	}
}

void Hal::SetPin(Pin aPin, std::variant<bool, float, std::string, int> aValue)
{
	auto it = pins.find(aPin);
	if (it != pins.end())
	{
		std::visit([&](auto &halpin)
				   { halpin.SetValue(aValue); }, it->second);
	}
	else
	{
		throw std::runtime_error("Pin not found: " + std::to_string(static_cast<int>(aPin)));
	}
}

std::variant<bool, float, std::string, int> Hal::GetPin(Pin aPin)
{
	auto it = pins.find(aPin);
	if (it != pins.end())
	{
		std::variant<bool, float, std::string, int> value;

		std::visit([&](auto &pin)
				   { value = pin.Get(); }, it->second);

		return value;
	}
	else
	{
		throw std::runtime_error("Pin not found: " + std::to_string(static_cast<int>(aPin)));
	}
}