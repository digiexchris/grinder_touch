#pragma once
#include <fstream>
#include <rapidjson/document.h>
#include <rapidjson/istreamwrapper.h>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>
#include <string>
#include <unordered_map>
#include <variant>

using Setting = std::variant<int, double, bool, std::string>;
class Settings
{
public:
	Settings(std::string aFilename);

	template <typename T>
	void Set(std::string aKey, T aValue);

	template <typename T>
	T Get(const std::string &aKey) const;

	void Save();

private:
	std::string myFilename;
	std::unordered_map<std::string, Setting> mySettings;
	void LoadFromFile();
};