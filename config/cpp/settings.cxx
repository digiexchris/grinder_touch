#include "settings.hxx"
#include <fstream>
#include <iostream>

SettingsManager *SettingsManager::myInstance = nullptr;

SettingsManager::SettingsManager(std::string aFilename) : myFilename(aFilename)
{
	mySettings = Load();
	myInstance = this;
}

std::shared_ptr<Settings> SettingsManager::Load()
{
	std::ifstream file(myFilename);
	if (!file.is_open())
	{
		std::cerr << "Failed to open settings file: " << myFilename << '\n';
		return nullptr;
	}

	nlohmann::json j;
	file >> j;

	auto settings = std::make_shared<Settings>();
	settings->from_json(j);
	file.close();

	return settings;
}

void SettingsManager::Save()
{
	std::ofstream file(myFilename);
	if (!file.is_open())
	{
		std::cerr << "Failed to open settings file for writing: " << myFilename << '\n';
		return;
	}

	nlohmann::json j = mySettings->to_json();
	file << j.dump(4); // Pretty print with 4 spaces
	file.close();
}

std::shared_ptr<Settings> SettingsManager::Get()
{
	return mySettings;
}

void Settings::from_json(const nlohmann::json &j)
{
	x_min = j["x_min"].get<double>();
	x_max = j["x_max"].get<double>();
	y_min = j["y_min"].get<double>();
	y_max = j["y_max"].get<double>();
	z_min = j["z_min"].get<double>();
	z_max = j["z_max"].get<double>();
	x_speed = j["x_speed"].get<uint32_t>();
	y_speed = j["y_speed"].get<uint32_t>();
	z_speed = j["z_speed"].get<uint32_t>();
	z_direction = j["z_direction"].get<bool>();
	z_crossfeed = j["z_crossfeed"].get<double>();
	y_downfeed = j["y_downfeed"].get<double>();
	enable_x = j["enable_x"].get<bool>();
	enable_y = j["enable_y"].get<bool>();
	enable_z = j["enable_z"].get<bool>();
	stop_at_z_limit = j["stop_at_z_limit"].get<bool>();
	crossfeed_at = j["crossfeed_at"].get<int32_t>();
	repeat_at = j["repeat_at"].get<int32_t>();
	is_running = j["is_running"].get<bool>();
	dress_start_x = j["dress_start_x"].get<double>();
	dress_start_y = j["dress_start_y"].get<double>();
	dress_start_z = j["dress_start_z"].get<double>();
	dress_end_x = j["dress_end_x"].get<double>();
	dress_end_y = j["dress_end_y"].get<double>();
	dress_end_z = j["dress_end_z"].get<double>();
	dress_stepover_x = j["dress_stepover_x"].get<double>();
	dress_stepover_y = j["dress_stepover_y"].get<double>();
	dress_stepover_z = j["dress_stepover_z"].get<double>();
	dress_wheel_rpm = j["dress_wheel_rpm"].get<double>();
	dress_wheel_dia = j["dress_wheel_dia"].get<double>();
	dress_point_dia = j["dress_point_dia"].get<double>();
	dress_offset_gcode = j["dress_offset_gcode"].get<std::string>();
}

nlohmann::json
Settings::to_json() const
{
	nlohmann::json j;
	j["x_min"] = x_min;
	j["x_max"] = x_max;
	j["y_min"] = y_min;
	j["y_max"] = y_max;
	j["z_min"] = z_min;
	j["z_max"] = z_max;
	j["x_speed"] = x_speed;
	j["y_speed"] = y_speed;
	j["z_speed"] = z_speed;
	j["z_direction"] = z_direction;
	j["z_crossfeed"] = z_crossfeed;
	j["y_downfeed"] = y_downfeed;
	j["enable_x"] = enable_x;
	j["enable_y"] = enable_y;
	j["enable_z"] = enable_z;
	j["stop_at_z_limit"] = stop_at_z_limit;
	j["crossfeed_at"] = crossfeed_at;
	j["repeat_at"] = repeat_at;
	j["is_running"] = is_running;
	j["dress_start_x"] = dress_start_x;
	j["dress_start_y"] = dress_start_y;
	j["dress_start_z"] = dress_start_z;
	j["dress_end_x"] = dress_end_x;
	j["dress_end_y"] = dress_end_y;
	j["dress_end_z"] = dress_end_z;
	j["dress_stepover_x"] = dress_stepover_x;
	j["dress_stepover_y"] = dress_stepover_y;
	j["dress_stepover_z"] = dress_stepover_z;
	j["dress_wheel_rpm"] = dress_wheel_rpm;
	j["dress_wheel_dia"] = dress_wheel_dia;
	j["dress_point_dia"] = dress_point_dia;
	j["dress_offset_gcode"] = dress_offset_gcode;
	return j;
}
