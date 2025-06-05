#pragma once

#include "linuxcnc/emc_nml.hh"
#include "settings.hxx"
#include "status.hxx"
#include <QObject>
#include <QTimer>
#include <array>
#include <atomic>
#include <memory>
#include <thread>

// Forward declarations
class EMC_STAT;
class NML;

// Grinder settings structure for GUI integration
struct GrinderSettings
{
	double x_min, x_max, y_min, y_max, z_min, z_max;
	double x_speed, y_speed, z_speed;
	double z_crossfeed, y_downfeed;
	bool enable_x, enable_y, enable_z;
	bool stop_at_z_limit;
	int crossfeed_at, repeat_at;
	double dress_start_x, dress_start_y, dress_start_z;
	double dress_end_x, dress_end_y, dress_end_z;
	double dress_stepover_x, dress_stepover_y, dress_stepover_z;
	double dress_wheel_rpm, dress_wheel_dia;
};

class GrinderMotion : public QObject
{
	Q_OBJECT

signals:
	void infoMessage(const QString &message);
	void errorMessage(const QString &message);
	void warningMessage(const QString &message);
	void positionChanged(double x, double y, double z);
	void machineStateChanged(LinuxCncStatus status);
	void grinderStarted();
	void grinderStopped();
	void settingsChanged();

public slots:
	void onJog(Axis axis, bool direction);
	void onJogStop(Axis axis);

private:
	bool isStandalone = false;
	QTimer *updateTimer;
	EMC_STAT *myEmcStatus;
	NML *error_channel;
	NML *command_channel;
	std::atomic<bool> is_running;
	std::atomic<bool> machine_ok;
	std::thread monitor_thread;
	bool grinder_should_monitor;
	bool is_first_run;
	bool downfeed_now;
	std::array<double, 9> current_pos; // current relative position
	SettingsManager *mySettingsManager;
	GrinderSettings grinder_settings;
	int command_serial_number = 0;

	void monitorStateImpl();
	void waitForMotionComplete();
	bool checkErrors();
	bool sendCommand(NMLmsg &msg);
	bool setMDIMode();
	void mainSequence();
	void moveInsideLimits();
	void downfeed();
	void loadSettings();
	void saveSettings();

public:
	GrinderMotion(SettingsManager *aSettingsManager, bool standaloneMode = false);
	~GrinderMotion();

	void Start();
	void monitorState();
	void initializeNML();
	void sendMDICommand(const char *command);
	bool canStart();
	void start();
	void stop();
	[[nodiscard]] bool getIsRunning() const;
	void cleanup();

	Position getCurrentPosition() const;

	void updatePosition();
	// bool getMachineOk() const;
	// void jogAxis(int axis, double velocity);
	// void stopJog();
	// void setSpindleSpeed(int rpm);
	// void setSpindleDirection(bool forward);
	// void stopSpindle();
	// void setFeedOverride(double percentage);
	// void setSpindleOverride(double percentage);
	// void setRapidOverride(double percentage);
	// void runGcodeFile(const std::string &filename);
	// void pauseProgram();
	// void stopProgram();
	// void homeAxis(int axis);
	// void homeAllAxes();
	// void touchoffAxis(int axis, double value);

	// Grinder-specific operations
	void startGrindingCycle();
	void stopGrindingCycle();
	void performDownfeed();

	// Settings management
	void updateSettings(const GrinderSettings &settings);
	GrinderSettings getSettings() const;
};
