#pragma once
// #include "linuxcnc/emc_nml.hh"
#include "linuxcnc/hal.h"

#include <cassert>
#include <functional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <variant>

enum class Pin
{
	// limits
	X_MIN = 0,
	X_MAX,
	Y_MIN,
	Y_MAX,
	Z_MIN,
	Z_MAX,

	// speeds
	X_SPEED,
	Y_SPEED,
	Z_SPEED,

	// enable grind features for axis
	ENABLE_X,
	ENABLE_Y,
	ENABLE_Z,

	// direction for reverse repeat type
	Z_DIRECTION,

	// stop once Z reaches the approaching limit
	STOP_AT_Z_LIMIT,

	// start/stop the grind cycle
	IS_RUNNING,

	// depth of cut/stepover
	Z_CROSSFEED,
	Y_DOWNFEED,

	// crossfeed at which X limit, and which repeat type when a Z limit is reached
	CROSSFEED_AT,
	REPEAT_AT,

	// request a downfeed immediately at the end of the current cycle
	DOWNFEED_NOW,

	NUM_PINS // This should always be the last item
};

template <typename T, typename Derived, typename BaseUnit>
struct HalPin
{
	using type = T;
	// T **address;
	std::string name;
	Pin pin;
	hal_pin_dir_t direction;

	HalPin(Pin aPin, std::string aName, hal_pin_dir_t aDirection) : name(aName), pin(aPin), direction(aDirection)
	{
	}

	void SetValue(std::variant<bool, float, std::string, int> aValue)
	{
		// static_cast<Derived *>(this)->Set(static_cast<BaseUnit>(aValue));

		std::visit([this](auto &&val)
				   {
        using Tp = std::decay_t<decltype(val)>;
        if constexpr (std::is_convertible_v<Tp, BaseUnit>) {
            static_cast<Derived*>(this)->Set(static_cast<BaseUnit>(val));
        } }, aValue);
	}

	// void GetValue(std::variant<bool, float, std::string, int> &aValue)
	// {
	// 	aValue = static_cast<Derived *>(this)->Get();
	// }
};

struct HalFloat : HalPin<hal_float_t, HalFloat, float>
{

	hal_float_t **address;
	HalFloat(Pin aPin, std::string aName, hal_pin_dir_t aDirection, std::string componentName, int componentId) : HalPin<hal_float_t, HalFloat, float>(aPin, aName, aDirection)
	{
		address = static_cast<hal_float_t **>(hal_malloc(sizeof(hal_float_t)));
		if (address == nullptr)
		{
			throw std::runtime_error("Failed to allocate HAL shared memory for float pin: " + aName);
		}
		assert(hal_pin_float_new((componentName + "." + name).c_str(),
								 direction,
								 address,
								 componentId) == 0);
	}

	void Set(float aValue)
	{
		**address = aValue;
	}

	float Get()
	{
		return **address;
	}
};

struct HalBit : HalPin<hal_bit_t, HalBit, bool>
{
	HalBit(Pin aPin, std::string aName, hal_pin_dir_t aDirection, std::string componentName, int componentId) : HalPin<hal_bit_t, HalBit, bool>(aPin, aName, aDirection)
	{
		address = static_cast<hal_bit_t **>(hal_malloc(sizeof(hal_bit_t)));
		if (address == nullptr)
		{
			throw std::runtime_error("Failed to allocate HAL shared memory for bit pin: " + aName);
		}
		assert(hal_pin_bit_new((componentName + "." + name).c_str(),
							   direction,
							   address,
							   componentId) == 0);
	}

	hal_bit_t **address;

	void Set(bool aValue)
	{
		**address = aValue;
	}

	bool Get()
	{
		return **address;
	}
};

// struct HalS32 : HalPin<hal_s32_t, HalS32, std::string>
// {
// 	HalS32(Pin aPin, std::string aName, hal_s32_t **anAddress, hal_pin_dir_t aDirection) : HalPin<hal_s32_t, HalS32, std::string>(aPin, aName, anAddress, aDirection)
// 	{
// 	}

// 	hal_s32_t **s32Address;

// 	void Create(std::string componentName, int componentId)
// 	{
// 		assert(hal_pin_s32_new((componentName + "." + name).c_str(),
// 							   direction,
// 							   address,
// 							   componentId) == 0);
// 	}

// 	void Set(std::string aValue)
// 	{
// 		**s32Address = std::stoi(aValue);
// 	}

// 	std::string Get()
// 	{
// 		return std::string(static_cast<char *>(**s32Address));
// 	}
// };

struct HalU32 : HalPin<hal_u32_t, HalU32, int>
{
	HalU32(Pin aPin, std::string aName, hal_pin_dir_t aDirection, std::string componentName, int componentId) : HalPin<hal_u32_t, HalU32, int>(aPin, aName, aDirection)
	{
		address = static_cast<hal_u32_t **>(hal_malloc(sizeof(hal_u32_t)));
		if (address == nullptr)
		{
			throw std::runtime_error("Failed to allocate HAL shared memory for u32 pin: " + aName);
		}
		assert(hal_pin_u32_new((componentName + "." + name).c_str(),
							   direction,
							   address,
							   componentId) == 0);
	}

	hal_u32_t **address;

	void Set(int aValue)
	{
		**address = aValue;
	}

	int Get()
	{
		return **address;
	}
};

// struct RawHalPins
// {
// 	hal_float_t *x_min, *x_max, *y_min, *y_max, *z_min, *z_max;
// 	hal_float_t *x_speed, *y_speed, *z_speed;
// 	hal_bit_t *z_direction, *enable_x, *enable_y, *enable_z;
// 	hal_bit_t *stop_at_z_limit, *is_running;
// 	hal_float_t *z_crossfeed, *y_downfeed;
// 	hal_u32_t *crossfeed_at, *repeat_at;
// 	hal_bit_t *downfeed_now;
// };

using HalType = std::variant<HalFloat, HalBit, /*HalS32,*/ HalU32>;

class Hal
{
public:
	Hal();
	~Hal();

	void SetPin(Pin aPin, std::variant<bool, float, std::string, int> aValue);

	std::variant<bool, float, std::string, int> GetPin(Pin aPin);

private:
	template <typename T>
	void CreatePin(Pin aPin, std::string aName, hal_pin_dir_t aDirection);

	std::unordered_map<Pin, HalType> pins;
	int componentId;

	const std::string componentName = "grinder";

	bool componentIsInitalized = false;
};