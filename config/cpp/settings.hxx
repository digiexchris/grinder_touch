#pragma once
#include <QObject>
#include <QString>
#include <memory>
#include <nlohmann/json.hpp>
#include <string>

#include "pins.hxx"

class Settings : public QObject
{
	Q_OBJECT

	Q_PROPERTY(double xMin READ XMin WRITE SetXMin NOTIFY XMinChanged)
	Q_PROPERTY(double xMax READ XMax WRITE SetXMax NOTIFY XMaxChanged)
	Q_PROPERTY(double yMin READ YMin WRITE SetYMin NOTIFY YMinChanged)
	Q_PROPERTY(double yMax READ YMax WRITE SetYMax NOTIFY YMaxChanged)
	Q_PROPERTY(double zMin READ ZMin WRITE SetZMin NOTIFY ZMinChanged)
	Q_PROPERTY(double zMax READ ZMax WRITE SetZMax NOTIFY ZMaxChanged)
	Q_PROPERTY(double xSpeed READ XSpeed WRITE SetXSpeed NOTIFY XSpeedChanged)
	Q_PROPERTY(double ySpeed READ YSpeed WRITE SetYSpeed NOTIFY YSpeedChanged)
	Q_PROPERTY(double zSpeed READ ZSpeed WRITE SetZSpeed NOTIFY ZSpeedChanged)
	Q_PROPERTY(bool zDirection READ ZDirection WRITE SetZDirection NOTIFY ZDirectionChanged)
	Q_PROPERTY(double zCrossfeed READ ZCrossfeed WRITE SetZCrossfeed NOTIFY ZCrossfeedChanged)
	Q_PROPERTY(double yDownfeed READ YDownfeed WRITE SetYDownfeed NOTIFY YDownfeedChanged)
	Q_PROPERTY(bool enableX READ EnableX WRITE SetEnableX NOTIFY EnableXChanged)
	Q_PROPERTY(bool enableY READ EnableY WRITE SetEnableY NOTIFY EnableYChanged)
	Q_PROPERTY(bool enableZ READ EnableZ WRITE SetEnableZ NOTIFY EnableZChanged)
	Q_PROPERTY(bool stopAtZLimit READ StopAtZLimit WRITE SetStopAtZLimit NOTIFY StopAtZLimitChanged)
	Q_PROPERTY(uint32_t crossfeedAt READ CrossfeedAt WRITE SetCrossfeedAt NOTIFY CrossfeedAtChanged)
	Q_PROPERTY(uint32_t repeatAt READ RepeatAt WRITE SetRepeatAt NOTIFY RepeatAtChanged)
	Q_PROPERTY(bool isRunning READ IsRunning WRITE SetIsRunning NOTIFY IsRunningChanged)
	Q_PROPERTY(double dressStartX READ DressStartX WRITE SetDressStartX NOTIFY DressStartXChanged)
	Q_PROPERTY(double dressStartY READ DressStartY WRITE SetDressStartY NOTIFY DressStartYChanged)
	Q_PROPERTY(double dressStartZ READ DressStartZ WRITE SetDressStartZ NOTIFY DressStartZChanged)
	Q_PROPERTY(double dressEndX READ DressEndX WRITE SetDressEndX NOTIFY DressEndXChanged)
	Q_PROPERTY(double dressEndY READ DressEndY WRITE SetDressEndY NOTIFY DressEndYChanged)
	Q_PROPERTY(double dressEndZ READ DressEndZ WRITE SetDressEndZ NOTIFY DressEndZChanged)
	Q_PROPERTY(double dressStepoverX READ DressStepoverX WRITE SetDressStepoverX NOTIFY DressStepoverXChanged)
	Q_PROPERTY(double dressStepoverY READ DressStepoverY WRITE SetDressStepoverY NOTIFY DressStepoverYChanged)
	Q_PROPERTY(double dressStepoverZ READ DressStepoverZ WRITE SetDressStepoverZ NOTIFY DressStepoverZChanged)
	Q_PROPERTY(double dressWheelRpm READ DressWheelRpm WRITE SetDressWheelRpm NOTIFY DressWheelRpmChanged)
	Q_PROPERTY(double dressWheelDia READ DressWheelDia WRITE SetDressWheelDia NOTIFY DressWheelDiaChanged)
	Q_PROPERTY(double dressPointDia READ DressPointDia WRITE SetDressPointDia NOTIFY DressPointDiaChanged)
	Q_PROPERTY(QString dressOffsetGcode READ GetDressOffsetGcodeQString WRITE SetDressOffsetGcodeQString NOTIFY DressOffsetGcodeChanged)

public:
	explicit Settings(QObject *aParent = nullptr);

	// Copy constructor
	Settings(const Settings &aOther) = delete;

	// Move constructor
	Settings(Settings &&aOther) = delete;

	// Copy assignment
	Settings &operator=(const Settings &aOther) = delete;

	// Move assignment
	Settings &operator=(Settings &&aOther) = delete;

	// Getters
	double XMin() const { return myXMin; }
	double XMax() const { return myXMax; }
	double YMin() const { return myYMin; }
	double YMax() const { return myYMax; }
	double ZMin() const { return myZMin; }
	double ZMax() const { return myZMax; }
	double XSpeed() const { return myXSpeed; }
	double YSpeed() const { return myYSpeed; }
	double ZSpeed() const { return myZSpeed; }
	bool ZDirection() const { return myZDirection; }
	double ZCrossfeed() const { return myZCrossfeed; }
	double YDownfeed() const { return myYDownfeed; }
	bool EnableX() const { return myEnableX; }
	bool EnableY() const { return myEnableY; }
	bool EnableZ() const { return myEnableZ; }
	bool StopAtZLimit() const { return myStopAtZLimit; }
	uint32_t CrossfeedAt() const { return myCrossfeedAt; }
	uint32_t RepeatAt() const { return myRepeatAt; }
	bool IsRunning() const { return myIsRunning; }
	double DressStartX() const { return myDressStartX; }
	double DressStartY() const { return myDressStartY; }
	double DressStartZ() const { return myDressStartZ; }
	double DressEndX() const { return myDressEndX; }
	double DressEndY() const { return myDressEndY; }
	double DressEndZ() const { return myDressEndZ; }
	double DressStepoverX() const { return myDressStepoverX; }
	double DressStepoverY() const { return myDressStepoverY; }
	double DressStepoverZ() const { return myDressStepoverZ; }
	double DressWheelRpm() const { return myDressWheelRpm; }
	double DressWheelDia() const { return myDressWheelDia; }
	double DressPointDia() const { return myDressPointDia; }

	// For Qt UI
	QString GetDressOffsetGcodeQString() const { return QString::fromStdString(myDressOffsetGcode); }
	void SetDressOffsetGcodeQString(const QString &aDressOffsetGcode);

	// For backend
	const std::string &GetDressOffsetGcode() const { return myDressOffsetGcode; }
	void SetDressOffsetGcode(const std::string &aDressOffsetGcode);

	// Setters
	void SetXMin(double aXMin);
	void SetXMax(double aXMax);
	void SetYMin(double aYMin);
	void SetYMax(double aYMax);
	void SetZMin(double aZMin);
	void SetZMax(double aZMax);
	void SetXSpeed(double aXSpeed);
	void SetYSpeed(double aYSpeed);
	void SetZSpeed(double aZSpeed);
	void SetZDirection(bool aZDirection);
	void SetZCrossfeed(double aZCrossfeed);
	void SetYDownfeed(double aYDownfeed);
	void SetEnableX(bool aEnableX);
	void SetEnableY(bool aEnableY);
	void SetEnableZ(bool aEnableZ);
	void SetStopAtZLimit(bool aStopAtZLimit);
	void SetCrossfeedAt(uint32_t aCrossfeedAt);
	void SetRepeatAt(uint32_t aRepeatAt);
	void SetIsRunning(bool aIsRunning);
	void SetDressStartX(double aDressStartX);
	void SetDressStartY(double aDressStartY);
	void SetDressStartZ(double aDressStartZ);
	void SetDressEndX(double aDressEndX);
	void SetDressEndY(double aDressEndY);
	void SetDressEndZ(double aDressEndZ);
	void SetDressStepoverX(double aDressStepoverX);
	void SetDressStepoverY(double aDressStepoverY);
	void SetDressStepoverZ(double aDressStepoverZ);
	void SetDressWheelRpm(double aDressWheelRpm);
	void SetDressWheelDia(double aDressWheelDia);
	void SetDressPointDia(double aDressPointDia);
	void SetDressOffsetGcode(const QString &aDressOffsetGcode);

	// Serialization
	nlohmann::json ToJson() const;
	void FromJson(const nlohmann::json &aJ);

signals:
	void XMinChanged(double);
	void XMaxChanged(double);
	void YMinChanged(double);
	void YMaxChanged(double);
	void ZMinChanged(double);
	void ZMaxChanged(double);
	void XSpeedChanged(double);
	void YSpeedChanged(double);
	void ZSpeedChanged(double);
	void ZDirectionChanged(bool);
	void ZCrossfeedChanged(double);
	void YDownfeedChanged(double);
	void EnableXChanged(bool);
	void EnableYChanged(bool);
	void EnableZChanged(bool);
	void StopAtZLimitChanged(bool);
	void CrossfeedAtChanged(uint32_t);
	void RepeatAtChanged(uint32_t);
	void IsRunningChanged(bool);
	void DressStartXChanged(double);
	void DressStartYChanged(double);
	void DressStartZChanged(double);
	void DressEndXChanged(double);
	void DressEndYChanged(double);
	void DressEndZChanged(double);
	void DressStepoverXChanged(double);
	void DressStepoverYChanged(double);
	void DressStepoverZChanged(double);
	void DressWheelRpmChanged(double);
	void DressWheelDiaChanged(double);
	void DressPointDiaChanged(double);
	void DressOffsetGcodeChanged(const QString &);

	// Custom signal emitters
	void AnyPropertyChanged(Pin aPin, std::variant<bool, double, std::string, uint32_t> aValue);

private:
	double myXMin = 0;
	double myXMax = 0;
	double myYMin = 0;
	double myYMax = 0;
	double myZMin = 0;
	double myZMax = 0;
	double myXSpeed = 0;
	double myYSpeed = 0;
	double myZSpeed = 0;
	bool myZDirection = false;
	double myZCrossfeed = 0;
	double myYDownfeed = 0;
	bool myEnableX = false;
	bool myEnableY = false;
	bool myEnableZ = false;
	bool myStopAtZLimit = false;
	uint32_t myCrossfeedAt = 0;
	uint32_t myRepeatAt = 0;
	bool myIsRunning = false;
	double myDressStartX = 0;
	double myDressStartY = 0;
	double myDressStartZ = 0;
	double myDressEndX = 0;
	double myDressEndY = 0;
	double myDressEndZ = 0;
	double myDressStepoverX = 0;
	double myDressStepoverY = 0;
	double myDressStepoverZ = 0;
	double myDressWheelRpm = 0;
	double myDressWheelDia = 0;
	double myDressPointDia = 0;
	std::string myDressOffsetGcode;
};

class SettingsManager : public QObject
{
	Q_OBJECT
public:
	explicit SettingsManager(std::string aFilename);

	std::shared_ptr<Settings> Load();
	void Save();
	std::shared_ptr<Settings> Get();

private:
	std::string myFilename;
	std::shared_ptr<Settings> mySettings;

	/*Since Settings emits signals that are consumed by this manager
	to trigger a save every time a setting changes, we need to disable
	that behaviour during loading otherwise SettingsManager will load
	and immediately save again, possibly making an infinite loop of the
	whole mess. It's still useful if SettingsManager saves any changes
	if a setting changes from another process while a load is occurring
	however. This flag manages that for the thread that's curringly doing
	the load. That leaves a small window where the system may not be runnign
	with the most up to date state that has been saved, but that's a
	problem for tomorrow Chris. It's already over-engineered probably.*/
	class ScopedSupressSave
	{
	public:
		ScopedSupressSave()
		{
			myIsSupressed = true;
		}

		~ScopedSupressSave()
		{
			myIsSupressed = false;
		}

	private:
		friend class SettingsManager;
		static thread_local bool myIsSupressed;
	};

	static bool IsSaveSuppressed()
	{
		return ScopedSupressSave::myIsSupressed;
	}
};