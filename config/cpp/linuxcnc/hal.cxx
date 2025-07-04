#include "hal.hxx"
#include "../pins.hxx"
#include "linuxcnc/hal.h"

#include <variant>

// #include <cassert>
// #include <csignal>
// #include <cstdlib>
// #include <cstring>
// #include <cxxabi.h>
#include <iostream>
#include <memory>
#include <stdexcept>
// #include <sstream>

template <typename T>
void Hal::CreatePin(Pin aPin, std::string aName, hal_pin_dir_t aDirection)
{
	// pins.try_emplace(aPin, T(aPin, aName, aDirection, componentName, componentId));

	// auto pinVariant = T(aPin, aName, aDirection, componentName, componentId);
	// pins.try_emplace(aPin, std::make_unique<T>(std::move(pinVariant)));

	pins.try_emplace(
		aPin,
		HalType{std::in_place_type<std::unique_ptr<T>>,
				std::make_unique<T>(aPin, aName, aDirection, componentName, componentId)});
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

	CreatePin<HalFloat>(Pin::XMin, "x_min", HAL_IN);
	CreatePin<HalFloat>(Pin::XMax, "x_max", HAL_IN);
	CreatePin<HalFloat>(Pin::YMin, "y_min", HAL_IN);
	CreatePin<HalFloat>(Pin::YMax, "y_max", HAL_IN);
	CreatePin<HalFloat>(Pin::ZMin, "z_min", HAL_IN);
	CreatePin<HalFloat>(Pin::ZMax, "z_max", HAL_IN);
	CreatePin<HalFloat>(Pin::XSpeed, "x_speed", HAL_IN);
	CreatePin<HalFloat>(Pin::YSpeed, "y_speed", HAL_IN);
	CreatePin<HalFloat>(Pin::ZSpeed, "z_speed", HAL_IN);
	CreatePin<HalBit>(Pin::ZDirection, "z_direction", HAL_IO);
	CreatePin<HalFloat>(Pin::ZCrossfeed, "z_crossfeed", HAL_IN);
	CreatePin<HalFloat>(Pin::YDownfeed, "y_downfeed", HAL_IN);
	CreatePin<HalBit>(Pin::EnableX, "enable_x", HAL_IO);
	CreatePin<HalBit>(Pin::EnableY, "enable_y", HAL_IO);
	CreatePin<HalBit>(Pin::EnableZ, "enable_z", HAL_IO);
	CreatePin<HalBit>(Pin::StopAtZLimit, "stop_at_z_limit", HAL_IN);
	CreatePin<HalU32>(Pin::CrossfeedAt, "crossfeed_at", HAL_IN);
	CreatePin<HalU32>(Pin::RepeatAt, "repeat_at", HAL_IN);
	CreatePin<HalBit>(Pin::IsRunning, "is_running", HAL_IO);
	CreatePin<HalBit>(Pin::DownfeedNow, "downfeed_now", HAL_IO);

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

void Hal::SetPin(Pin aPin, std::variant<bool, double, std::string, uint32_t> aValue)
{
	auto it = pins.find(aPin);
	if (it != pins.end())
	{
		std::visit([&](auto &halpin)
				   { halpin->SetValue(aValue); }, it->second);
	}
	else
	{
		throw std::runtime_error("Pin not found: " + std::to_string(static_cast<int>(aPin)));
	}
}

std::variant<bool, double, std::string, uint32_t> Hal::GetPin(Pin aPin)
{
	auto it = pins.find(aPin);
	if (it != pins.end())
	{
		std::variant<bool, double, std::string, uint32_t> value;

		std::visit([&](auto &pin)
				   { value = pin->Get(); }, it->second);

		return value;
	}
	else
	{
		throw std::runtime_error("Pin not found: " + std::to_string(static_cast<int>(aPin)));
	}
}