#pragma once
#include <nlohmann/json.hpp>
#include <string>
#include <unordered_map>
#include <variant>

// using Setting = std::variant<int, double, bool, std::string>;
struct Settings
{
	double x_min;
	double x_max;
	double y_min;
	double y_max;
	double z_min;
	double z_max;
	uint32_t x_speed;
	uint32_t y_speed;
	uint32_t z_speed;
	bool z_direction;
	double z_crossfeed;
	double y_downfeed;
	bool enable_x;
	bool enable_y;
	bool enable_z;
	bool stop_at_z_limit;
	int32_t crossfeed_at;
	int32_t repeat_at;
	bool is_running;
	double dress_start_x;
	double dress_start_y;
	double dress_start_z;
	double dress_end_x;
	double dress_end_y;
	double dress_end_z;
	double dress_stepover_x;
	double dress_stepover_y;
	double dress_stepover_z;
	double dress_wheel_rpm;
	double dress_wheel_dia;
	double dress_point_dia;
	std::string dress_offset_gcode;

	nlohmann::json to_json() const;
	void from_json(const nlohmann::json &j);
};

class SettingsManager
{
public:
	SettingsManager(std::string aFilename);
	static SettingsManager *GetInstance()
	{
		if (myInstance == nullptr)
		{
			myInstance = new SettingsManager("grinder_settings.json");
		}
		return myInstance;
	}

	std::shared_ptr<Settings> Load();
	void Save();
	/**
	@brief Return previously retrieved settings */
	std::shared_ptr<Settings> Get();
	std::shared_ptr<Settings> mySettings;

private:
	std::string myFilename;
	static SettingsManager *myInstance;
};