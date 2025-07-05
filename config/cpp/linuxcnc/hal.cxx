#include "hal.hxx"
#include "../pins.hxx"
#include "linuxcnc/hal.h"

#include <variant>
#include <iostream>
#include <memory>
#include <stdexcept>

template <typename T>
void Hal::CreatePin(Pin aPin, std::string aName, hal_pin_dir_t aDirection)
{
	pins.try_emplace(
		aPin,
		HalType{std::in_place_type<std::unique_ptr<T>>,
				std::make_unique<T>(aPin, aName, aDirection, componentName, componentId)});
}

Hal::Hal()
{
	componentId = hal_init(componentName.c_str());

	if (componentId < 0)
	{
		std::cout << "Failed to initialize HAL component" << std::to_string(componentId) << "\n";
		throw std::runtime_error("Failed to initialize HAL component: " + std::to_string(componentId));
	}

	componentIsInitalized = true;

	const std::string prefix = std::string(componentName) + ".";

	CreatePin<HalFloat>(Pin::XMin, "x_min", HAL_IO);
	CreatePin<HalFloat>(Pin::XMax, "x_max", HAL_IO);
	CreatePin<HalFloat>(Pin::YMin, "y_min", HAL_IO);
	CreatePin<HalFloat>(Pin::YMax, "y_max", HAL_IO);
	CreatePin<HalFloat>(Pin::ZMin, "z_min", HAL_IO);
	CreatePin<HalFloat>(Pin::ZMax, "z_max", HAL_IO);
	CreatePin<HalFloat>(Pin::XSpeed, "x_speed", HAL_IO);
	CreatePin<HalFloat>(Pin::YSpeed, "y_speed", HAL_IO);
	CreatePin<HalFloat>(Pin::ZSpeed, "z_speed", HAL_IO);
	CreatePin<HalBit>(Pin::ZDirection, "z_direction", HAL_IO);
	CreatePin<HalFloat>(Pin::ZCrossfeed, "z_crossfeed", HAL_IO);
	CreatePin<HalFloat>(Pin::YDownfeed, "y_downfeed", HAL_IO);
	CreatePin<HalBit>(Pin::EnableX, "enable_x", HAL_IO);
	CreatePin<HalBit>(Pin::EnableY, "enable_y", HAL_IO);
	CreatePin<HalBit>(Pin::EnableZ, "enable_z", HAL_IO);
	CreatePin<HalBit>(Pin::StopAtZLimit, "stop_at_z_limit", HAL_IO);
	CreatePin<HalU32>(Pin::CrossfeedAt, "crossfeed_at", HAL_IO);
	CreatePin<HalU32>(Pin::RepeatAt, "repeat_at", HAL_IO);
	CreatePin<HalBit>(Pin::IsRunning, "is_running", HAL_IO);
	CreatePin<HalBit>(Pin::DownfeedNow, "downfeed_now", HAL_IO);

	// hal.SetPin(Pin::ZDirection, true);
	// hal.SetPin(Pin::DownfeedNow, false);
	// hal.SetPin(Pin::IsRunning, false);

	// // Setting to the defaults. Expect that the settings aren't loaded yet.
	// hal.SetPin(Pin::XMin, 0.0);
	// hal.SetPin(Pin::XMax, 0.0);
	// hal.SetPin(Pin::YMin, 0.0);
	// hal.SetPin(Pin::YMax, 0.0);
	// hal.SetPin(Pin::ZMin, 0.0);
	// hal.SetPin(Pin::ZMax, 0.0);
	// hal.SetPin(Pin::XSpeed, 0.0);
	// hal.SetPin(Pin::YSpeed, 0.0);
	// hal.SetPin(Pin::ZSpeed, 0.0);
	// hal.SetPin(Pin::ZCrossfeed, 0.0);
	// hal.SetPin(Pin::YDownfeed, 0.0);
	// hal.SetPin(Pin::EnableX, false);
	// hal.SetPin(Pin::EnableY, false);
	// hal.SetPin(Pin::EnableZ, false);
	// hal.SetPin(Pin::StopAtZLimit, false);
	// hal.SetPin(Pin::CrossfeedAt, static_cast<uint32_t>(0));
	// hal.SetPin(Pin::RepeatAt, static_cast<uint32_t>(0));

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