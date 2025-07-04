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

// #include "grinder_motion.hxx"
#include "gui_events.hxx"
#include "linuxcnc/machine.hxx"
#include "settings.hxx"

#include "ui_grinder_touch.h" // Generated from grinder_touch.ui

class GrinderMainWindow : public QMainWindow
{
	Q_OBJECT

public:
	explicit GrinderMainWindow(QMainWindow *parent = nullptr, bool standaloneMode = false);
	~GrinderMainWindow();

public slots:
	void onInfoMessage(const QString &message);
	void onErrorMessage(const QString &message);
	void onWarningMessage(const QString &message);
	void onPositionChanged(const Position &pos);
	void onEstopClicked();
	void onEstopChanged(bool isActive);
	void onPowerClicked();
	void onHomedClicked();

protected:
	// signal processing
	void closeEvent(QCloseEvent *event) override;

signals:
	void infoMessage(const QString &message);
	void errorMessage(const QString &message);
	void warningMessage(const QString &message);
	void jog(Axis axis, bool direction);
	void jogStop();

private:
	// Grind tab slots
	void onGrindStartStop();

	// Sidebar slots
	void onExitClicked();

	// jog
	void onJogPressed(Axis axis, bool direction); // common function for all jogs
	void onJogXPlusPressed();
	void onJogXMinusPressed();
	void onJogYPlusPressed();
	void onJogYMinusPressed();
	void onJogZPlusPressed();
	void onJogZMinusPressed();
	// jog stop
	void onJogReleased();

	void onJogStopClicked();

	void on_clearErrorsPb_clicked();
	void on_errorsPte_textChanged();

	void loadStyleSheet();
	void connectSignals();
	void setupMenus();

	// Backend integration
	void initializeGrinderBackend();

	// Helper methods
	void showError(const QString &message);
	void showWarning(const QString &message);
	void showInfo(const QString &message);
	QString formatPosition(double pos, int precision = 4);

	Ui_MainWindow ui;

	// // Backend components
	// std::unique_ptr<GrinderMotion> motion;
	std::unique_ptr<SettingsManager> settingsManager;

	Machine *machine;

	// Application state
	bool isInitialized;
	bool isShuttingDown;
	bool m_standaloneMode;
};
