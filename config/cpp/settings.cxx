#include "settings.hxx"
#include <fstream>
#include <iostream>

Settings::Settings(QObject *aParent) : QObject(aParent) {}

#define SETTER_IMPL(TYPE, NAME, SIGNAL)    \
	void Settings::Set##NAME(TYPE a##NAME) \
	{                                      \
		if (my##NAME != a##NAME)           \
		{                                  \
			my##NAME = a##NAME;            \
			emit SIGNAL(a##NAME);          \
			emit AnyPropertyChanged();     \
		}                                  \
	}

SETTER_IMPL(double, XMin, XMinChanged)
SETTER_IMPL(double, XMax, XMaxChanged)
SETTER_IMPL(double, YMin, YMinChanged)
SETTER_IMPL(double, YMax, YMaxChanged)
SETTER_IMPL(double, ZMin, ZMinChanged)
SETTER_IMPL(double, ZMax, ZMaxChanged)
SETTER_IMPL(uint32_t, XSpeed, XSpeedChanged)
SETTER_IMPL(uint32_t, YSpeed, YSpeedChanged)
SETTER_IMPL(uint32_t, ZSpeed, ZSpeedChanged)
SETTER_IMPL(bool, ZDirection, ZDirectionChanged)
SETTER_IMPL(double, ZCrossfeed, ZCrossfeedChanged)
SETTER_IMPL(double, YDownfeed, YDownfeedChanged)
SETTER_IMPL(bool, EnableX, EnableXChanged)
SETTER_IMPL(bool, EnableY, EnableYChanged)
SETTER_IMPL(bool, EnableZ, EnableZChanged)
SETTER_IMPL(bool, StopAtZLimit, StopAtZLimitChanged)
SETTER_IMPL(uint32_t, CrossfeedAt, CrossfeedAtChanged)
SETTER_IMPL(uint32_t, RepeatAt, RepeatAtChanged)
SETTER_IMPL(bool, IsRunning, IsRunningChanged)
SETTER_IMPL(double, DressStartX, DressStartXChanged)
SETTER_IMPL(double, DressStartY, DressStartYChanged)
SETTER_IMPL(double, DressStartZ, DressStartZChanged)
SETTER_IMPL(double, DressEndX, DressEndXChanged)
SETTER_IMPL(double, DressEndY, DressEndYChanged)
SETTER_IMPL(double, DressEndZ, DressEndZChanged)
SETTER_IMPL(double, DressStepoverX, DressStepoverXChanged)
SETTER_IMPL(double, DressStepoverY, DressStepoverYChanged)
SETTER_IMPL(double, DressStepoverZ, DressStepoverZChanged)
SETTER_IMPL(double, DressWheelRpm, DressWheelRpmChanged)
SETTER_IMPL(double, DressWheelDia, DressWheelDiaChanged)
SETTER_IMPL(double, DressPointDia, DressPointDiaChanged)

void Settings::SetDressOffsetGcodeQString(const QString &aDressOffsetGcode)
{
	std::string newVal = aDressOffsetGcode.toStdString();
	if (myDressOffsetGcode != newVal)
	{
		myDressOffsetGcode = newVal;
		emit DressOffsetGcodeChanged(aDressOffsetGcode);
		emit AnyPropertyChanged();
	}
}

void Settings::SetDressOffsetGcode(const std::string &aDressOffsetGcode)
{
	if (myDressOffsetGcode != aDressOffsetGcode)
	{
		myDressOffsetGcode = aDressOffsetGcode;
		emit DressOffsetGcodeChanged(QString::fromStdString(aDressOffsetGcode));
		emit AnyPropertyChanged();
	}
}

nlohmann::json Settings::ToJson() const
{
	nlohmann::json j;
	j["x_min"] = myXMin;
	j["x_max"] = myXMax;
	j["y_min"] = myYMin;
	j["y_max"] = myYMax;
	j["z_min"] = myZMin;
	j["z_max"] = myZMax;
	j["x_speed"] = myXSpeed;
	j["y_speed"] = myYSpeed;
	j["z_speed"] = myZSpeed;
	j["z_direction"] = myZDirection;
	j["z_crossfeed"] = myZCrossfeed;
	j["y_downfeed"] = myYDownfeed;
	j["enable_x"] = myEnableX;
	j["enable_y"] = myEnableY;
	j["enable_z"] = myEnableZ;
	j["stop_at_z_limit"] = myStopAtZLimit;
	j["crossfeed_at"] = myCrossfeedAt;
	j["repeat_at"] = myRepeatAt;
	j["is_running"] = myIsRunning;
	j["dress_start_x"] = myDressStartX;
	j["dress_start_y"] = myDressStartY;
	j["dress_start_z"] = myDressStartZ;
	j["dress_end_x"] = myDressEndX;
	j["dress_end_y"] = myDressEndY;
	j["dress_end_z"] = myDressEndZ;
	j["dress_stepover_x"] = myDressStepoverX;
	j["dress_stepover_y"] = myDressStepoverY;
	j["dress_stepover_z"] = myDressStepoverZ;
	j["dress_wheel_rpm"] = myDressWheelRpm;
	j["dress_wheel_dia"] = myDressWheelDia;
	j["dress_point_dia"] = myDressPointDia;
	j["dress_offset_gcode"] = myDressOffsetGcode.toStdString();
	return j;
}

void Settings::FromJson(const nlohmann::json &aJ)
{
	if (aJ.contains("x_min"))
		SetXMin(aJ["x_min"].get<double>());
	if (aJ.contains("x_max"))
		SetXMax(aJ["x_max"].get<double>());
	if (aJ.contains("y_min"))
		SetYMin(aJ["y_min"].get<double>());
	if (aJ.contains("y_max"))
		SetYMax(aJ["y_max"].get<double>());
	if (aJ.contains("z_min"))
		SetZMin(aJ["z_min"].get<double>());
	if (aJ.contains("z_max"))
		SetZMax(aJ["z_max"].get<double>());
	if (aJ.contains("x_speed"))
		SetXSpeed(aJ["x_speed"].get<uint32_t>());
	if (aJ.contains("y_speed"))
		SetYSpeed(aJ["y_speed"].get<uint32_t>());
	if (aJ.contains("z_speed"))
		SetZSpeed(aJ["z_speed"].get<uint32_t>());
	if (aJ.contains("z_direction"))
		SetZDirection(aJ["z_direction"].get<bool>());
	if (aJ.contains("z_crossfeed"))
		SetZCrossfeed(aJ["z_crossfeed"].get<double>());
	if (aJ.contains("y_downfeed"))
		SetYDownfeed(aJ["y_downfeed"].get<double>());
	if (aJ.contains("enable_x"))
		SetEnableX(aJ["enable_x"].get<bool>());
	if (aJ.contains("enable_y"))
		SetEnableY(aJ["enable_y"].get<bool>());
	if (aJ.contains("enable_z"))
		SetEnableZ(aJ["enable_z"].get<bool>());
	if (aJ.contains("stop_at_z_limit"))
		SetStopAtZLimit(aJ["stop_at_z_limit"].get<bool>());
	if (aJ.contains("crossfeed_at"))
		SetCrossfeedAt(aJ["crossfeed_at"].get<uint32_t>());
	if (aJ.contains("repeat_at"))
		SetRepeatAt(aJ["repeat_at"].get<uint32_t>());
	if (aJ.contains("is_running"))
		SetIsRunning(aJ["is_running"].get<bool>());
	if (aJ.contains("dress_start_x"))
		SetDressStartX(aJ["dress_start_x"].get<double>());
	if (aJ.contains("dress_start_y"))
		SetDressStartY(aJ["dress_start_y"].get<double>());
	if (aJ.contains("dress_start_z"))
		SetDressStartZ(aJ["dress_start_z"].get<double>());
	if (aJ.contains("dress_end_x"))
		SetDressEndX(aJ["dress_end_x"].get<double>());
	if (aJ.contains("dress_end_y"))
		SetDressEndY(aJ["dress_end_y"].get<double>());
	if (aJ.contains("dress_end_z"))
		SetDressEndZ(aJ["dress_end_z"].get<double>());
	if (aJ.contains("dress_stepover_x"))
		SetDressStepoverX(aJ["dress_stepover_x"].get<double>());
	if (aJ.contains("dress_stepover_y"))
		SetDressStepoverY(aJ["dress_stepover_y"].get<double>());
	if (aJ.contains("dress_stepover_z"))
		SetDressStepoverZ(aJ["dress_stepover_z"].get<double>());
	if (aJ.contains("dress_wheel_rpm"))
		SetDressWheelRpm(aJ["dress_wheel_rpm"].get<double>());
	if (aJ.contains("dress_wheel_dia"))
		SetDressWheelDia(aJ["dress_wheel_dia"].get<double>());
	if (aJ.contains("dress_point_dia"))
		SetDressPointDia(aJ["dress_point_dia"].get<double>());
	if (aJ.contains("dress_offset_gcode"))
		SetDressOffsetGcode(QString::fromStdString(aJ["dress_offset_gcode"].get<std::string>()));
}

// --- SettingsManager ---

SettingsManager *SettingsManager::myInstance = nullptr;

SettingsManager::SettingsManager(std::string aFilename)
	: QObject(nullptr), myFilename(std::move(aFilename))
{
	mySettings = Load();
	if (mySettings)
	{
		QObject::connect(mySettings.get(), &Settings::AnyPropertyChanged, [this]()
						 { this->Save(); });
	}
}

std::shared_ptr<Settings> SettingsManager::Load()
{
	auto settings = std::make_shared<Settings>();
	std::ifstream inFile(myFilename);
	if (inFile)
	{
		nlohmann::json j;
		inFile >> j;
		settings->FromJson(j);
	}
	mySettings = settings;
	return settings;
}

void SettingsManager::Save()
{
	if (!mySettings)
		return;
	std::ofstream outFile(myFilename);
	if (outFile)
	{
		nlohmann::json j = mySettings->ToJson();
		outFile << j.dump(4);
	}
}

std::shared_ptr<Settings> SettingsManager::Get()
{
	return mySettings;
}