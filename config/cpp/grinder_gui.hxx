#pragma once

#include <QCheckBox>
#include <QComboBox>
#include <QDoubleSpinBox>
#include <QFile>
#include <QGridLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QMainWindow>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSlider>
#include <QSpinBox>
#include <QTabWidget>
#include <QTimer>
#include <QUiLoader>
#include <QVBoxLayout>
#include <QWidget>
#include <memory>

#include "grinder_motion_gui.hxx"
#include "settings.hxx"

class GrinderMainWindow : public QMainWindow
{
	Q_OBJECT

public:
	explicit GrinderMainWindow(QWidget *parent = nullptr, bool standaloneMode = false);
	~GrinderMainWindow();

protected:
	void closeEvent(QCloseEvent *event) override;
	void showEvent(QShowEvent *event) override;

private slots:
	// UI Update slots
	void updateStatus();
	void updatePositions();
	void updateErrors();

	// Grind tab slots
	void onGrindStartStop();
	void onGrindParametersChanged();

	// Dress tab slots
	void onDressStartStop();
	void onDressParametersChanged();

	// Gcode tab slots
	void onGcodeFileOpen();
	void onGcodeRun();
	void onGcodePause();
	void onGcodeStop();
	void onFeedOverrideChanged(int value);
	void onSpindleOverrideChanged(int value);
	void onRapidOverrideChanged(int value);

	// Manual/Jog tab slots
	void onJogModeChanged();
	void onJogVelocityChanged();
	void onJogAxisPlus(int axis);
	void onJogAxisMinus(int axis);
	void onSpindleForward();
	void onSpindleReverse();
	void onSpindleStop();
	void onSpindleSpeedChanged();

	// MDI tab slots
	void onMdiCommand();
	void onMdiHistorySelection();

	// Menu actions
	void onFileOpen();
	void onFileEdit();
	void onFileReload();
	void onFileQuit();
	void onMachineEstop();
	void onMachinePower();
	void onToolEditTable();
	void onToolReloadTable();
	void onViewHalMeter();
	void onViewHalScope();
	void onViewShowHal();

private:
	// UI Loading and setup
	void loadUiFile();
	void loadStyleSheet();
	void connectSignals();
	void setupWidgetReferences();
	void updateWidgetStates();
	void setupMenus();

	// Backend integration
	void initializeGrinderBackend();
	void startStatusUpdates();
	void stopStatusUpdates();

	// Helper methods
	void showError(const QString &message);
	void showInfo(const QString &message);
	QString formatPosition(double pos, int precision = 4);
	void updateMachineStatus();
	void updateGrindStatus();
	void updateSpindleStatus();

	// UI Components
	QWidget *m_centralWidget;
	QTabWidget *m_tabWidget;

	// Status update timer
	QTimer *m_statusTimer;

	// Backend components
	std::unique_ptr<GrinderMotionGui> m_grinderMotion;
	std::unique_ptr<SettingsManager> m_settingsManager;

	// UI Widget references (populated after loading UI file)
	// Positions
	QLabel *m_actualLbX;
	QLabel *m_actualLbY;
	QLabel *m_actualLbZ;

	// Overrides
	QSlider *m_feedOverrideSl;
	QSlider *m_spindleOverrideSl;
	QSlider *m_rapidOverrideSl;
	QLabel *m_feedOverrideLb;
	QLabel *m_spindleOverride0Lb;
	QLabel *m_rapidOverrideLb;

	// Jogging
	QComboBox *m_jogModesCb;
	QSlider *m_jogVelSl;
	QLabel *m_jogVelLb;
	QLabel *m_minJogVelLb;
	QLabel *m_maxJogVelLb;
	QPushButton *m_jogPlusPb0;
	QPushButton *m_jogMinusPb0;
	QPushButton *m_jogPlusPb1;
	QPushButton *m_jogMinusPb1;
	QPushButton *m_jogPlusPb2;
	QPushButton *m_jogMinusPb2;

	// Spindle
	QPushButton *m_spindleFwdPb;
	QPushButton *m_spindleRevPb;
	QPushButton *m_spindleStopPb;
	QSpinBox *m_spindleSpeedSb;
	QLabel *m_settingsSpeedLb;

	// Gcode
	QPlainTextEdit *m_gcodePte;
	QPushButton *m_optionalStopPb;
	QLabel *m_toolInSpindleLb;

	// Status
	QLabel *m_taskModeLb;
	QLabel *m_taskStateLb;
	QLabel *m_motionModeLb;
	QLabel *m_interpStateLb;
	QLabel *m_gcodesLb;
	QLabel *m_mcodesLb;
	QPlainTextEdit *m_errorsPte;
	QPushButton *m_clearErrorsPb;

	// Plot widget placeholder
	QWidget *m_plotWidget;

	// View checkboxes for plot options
	QCheckBox *m_viewDroCb;
	QCheckBox *m_viewExtentsOptionCb;
	QCheckBox *m_viewToolCb;
	QCheckBox *m_viewDtgCb;
	QCheckBox *m_viewLimitsCb;
	QCheckBox *m_viewLivePlotCb;
	QCheckBox *m_viewMetricUnitsCb;
	QCheckBox *m_viewOffsetsCb;
	QCheckBox *m_viewOverlayCb;
	QCheckBox *m_viewVelocityCb;
	QCheckBox *m_viewProgramCb;
	QCheckBox *m_viewRapidsCb;

	// Application state
	bool m_isInitialized;
	bool m_isShuttingDown;
	bool m_standaloneMode;
};
