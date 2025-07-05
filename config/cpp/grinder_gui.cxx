#include "grinder_gui.hxx"
#include <QApplication>
#include <QCloseEvent>
#include <QDir>
#include <QFileDialog>
#include <QMenuBar>
#include <QMessageBox>
#include <QShowEvent>
#include <QStandardPaths>
#include <QStatusBar>
#include <QTextStream>
#include <iostream>

#include "linuxcnc/machine.hxx"

GrinderMainWindow::GrinderMainWindow(QMainWindow *parent, bool standaloneMode)
	: QMainWindow(parent), isInitialized(false), isShuttingDown(false), m_standaloneMode(standaloneMode)
{
	if (m_standaloneMode)
	{
		setWindowTitle("Grinder Touch - Standalone Mode (UI Only)");
	}
	else
	{
		setWindowTitle("Grinder Touch - LinuxCNC GUI");
	}
	// setMinimumSize(800, 600);

	ui.setupUi(this);
	loadStyleSheet();
	setupMenus();

	settingsManager = std::make_unique<SettingsManager>("./grinder_settings.json");

	// Initialize machine and connect signals to Settings
	machine = new Machine(settingsManager->Get());

	// Initialize grinder motion controller
	// motion = std::make_unique<GrinderMotion>(settingsManager.get());

	// Connect gui signals
	connectSignals();

	// Load from config, trigger a gui update and machine/hal update
	settingsManager->Load();

	// if (!m_standaloneMode)
	// {
	// 	// Initialize the grinder backend only in LinuxCNC mode
	// 	motion->Start();
	// }
	// else
	// {
	// 	std::cout << "Standalone mode: Skipping LinuxCNC backend initialization" << std::endl;

	// 	// emit infoMessage("Grinder GUI initialized in standalone mode");
	// }

	machine->start();

	isInitialized = true;

	std::cout << "Grinder Touch GUI initialized successfully" << std::endl;
}

void GrinderMainWindow::onExitClicked()
{
	if (isShuttingDown)
	{
		return; // Already shutting down
	}

	// emit infoMessage("Exiting Grinder Touch GUI...");

	close(); // This will trigger the closeEvent
}

GrinderMainWindow::~GrinderMainWindow()
{
	isShuttingDown = true;

	if (!m_standaloneMode)
	{

		// if (motion)
		// {
		// 	motion->stop();
		// 	motion->cleanup();
		// }

		if (machine)
		{
			delete machine;
		}
	}
}

void GrinderMainWindow::loadStyleSheet()
{
	QFile styleFile("touch.qss");

	if (!styleFile.open(QIODevice::ReadOnly))
	{
		// Try alternative paths
		QStringList searchPaths = {
			"./touch.qss",
			"../touch.qss",
			QDir::currentPath() + "/touch.qss"};

		bool found = false;
		for (const QString &path : searchPaths)
		{
			styleFile.setFileName(path);
			if (styleFile.open(QIODevice::ReadOnly))
			{
				found = true;
				std::cout << "Found QSS file at: " << path.toStdString() << std::endl;
				break;
			}
		}

		if (!found)
		{
			std::cout << "Warning: Could not find touch.qss file, using default styling" << std::endl;
			return;
		}
	}
	QTextStream stream(&styleFile);
	QString styleSheet = stream.readAll();
	styleFile.close();

	// Apply the stylesheet to the application
	qApp->setStyleSheet(styleSheet);

	std::cout << "QSS stylesheet loaded successfully" << std::endl;
}

void GrinderMainWindow::setupMenus()
{
	// The UI file should already have menus defined, but we can add actions here
	// if needed or connect existing menu items

	// File menu actions would be connected here
	// Machine menu actions would be connected here
	// etc.
}

void GrinderMainWindow::connectSignals()
{

	Settings *settings = settingsManager->Get().get();
	// connect(motion.get(), &GrinderMotion::infoMessage, this, &GrinderMainWindow::onInfoMessage);
	// connect(motion.get(), &GrinderMotion::errorMessage, this, &GrinderMainWindow::onErrorMessage);
	// connect(motion.get(), &GrinderMotion::warningMessage, this, &GrinderMainWindow::onWarningMessage);

	// Machine status
	connect(ui.quit_pb, &QPushButton::clicked, this, &GrinderMainWindow::onExitClicked);
	connect(ui.estop_pb, &QPushButton::clicked, this, &GrinderMainWindow::onEstopClicked);
	// connect(machine, &Machine::positionChanged, this, &GrinderMainWindow::onPositionChanged);
	// connect(machine, &Machine::estopChanged, this, &GrinderMainWindow::onEstopChanged);
	connect(ui.power_pb, &QPushButton::clicked, this, &GrinderMainWindow::onPowerClicked);
	connect(ui.home_all_pb, &QPushButton::clicked, this, &GrinderMainWindow::onHomedClicked);

	// Grind Parameters

	// XMin
	connect(settings, &Settings::XMinChanged, [this](double value)
			{ ui.x_min_edit->setValue(value); });
	connect(ui.x_min_edit, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetXMin);

	// XMax
	connect(settings, &Settings::XMaxChanged, [this](double value)
			{ ui.x_max_edit->setValue(value); });
	connect(ui.x_max_edit, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetXMax);

	// YMin
	connect(settings, &Settings::YMinChanged, [this](double value)
			{ ui.y_min_edit->setValue(value); });
	connect(ui.y_min_edit, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetYMin);

	// YMax
	connect(settings, &Settings::YMaxChanged, [this](double value)
			{ ui.y_max_edit->setValue(value); });
	connect(ui.y_max_edit, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetYMax);

	// ZMin
	connect(settings, &Settings::ZMinChanged, [this](double value)
			{ ui.z_min_edit->setValue(value); });
	connect(ui.z_min_edit, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetZMin);

	// ZMax
	connect(settings, &Settings::ZMaxChanged, [this](double value)
			{ ui.z_max_edit->setValue(value); });
	connect(ui.z_max_edit, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetZMax);

	// XSpeed
	connect(settings, &Settings::XSpeedChanged, [this](double value)
			{ ui.x_speed_sb->setValue(value); });
	connect(ui.x_speed_sb, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetXSpeed);

	// YSpeed
	connect(settings, &Settings::YSpeedChanged, [this](double value)
			{ ui.y_speed_sb->setValue(value); });
	connect(ui.y_speed_sb, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetYSpeed);

	// ZSpeed
	connect(settings, &Settings::ZSpeedChanged, [this](double value)
			{ ui.z_speed_sb->setValue(value); });
	connect(ui.z_speed_sb, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetZSpeed);

	// ZDirection
	// 	    connect(settings, &Settings::ZDirectionChanged, [this](bool value)
	//    { ui.z_direction_cb->setChecked(value); });
	// 	connect(ui.z_direction_cb, &QCheckBox::toggled, settings, &Settings::SetZDirection);

	// ZCrossfeed
	connect(settings, &Settings::ZCrossfeedChanged, [this](double value)
			{ ui.z_crossfeed_sb->setValue(value); });
	connect(ui.z_crossfeed_sb, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetZCrossfeed);

	// YDownfeed
	connect(settings, &Settings::YDownfeedChanged, [this](double value)
			{ ui.y_downfeed_sb->setValue(value); });
	connect(ui.y_downfeed_sb, QOverload<double>::of(&QDoubleSpinBox::valueChanged), settings, &Settings::SetYDownfeed);

	// EnableX
	connect(settings, &Settings::EnableXChanged, [this](bool value)
			{ ui.enable_x_pb->setChecked(value); });
	connect(ui.enable_x_pb, &QCheckBox::toggled, settings, &Settings::SetEnableX);

	// EnableY
	connect(settings, &Settings::EnableYChanged, [this](bool value)
			{ ui.enable_y_pb->setChecked(value); });
	connect(ui.enable_y_pb, &QCheckBox::toggled, settings, &Settings::SetEnableY);

	// EnableZ
	connect(settings, &Settings::EnableZChanged, [this](bool value)
			{ ui.enable_z_pb->setChecked(value); });
	connect(ui.enable_z_pb, &QCheckBox::toggled, settings, &Settings::SetEnableZ);

	// StopAtZLimit
	connect(settings, &Settings::StopAtZLimitChanged, [this](bool value)
			{ ui.stop_at_z_limit_pb->setChecked(value); });
	connect(ui.stop_at_z_limit_pb, &QCheckBox::toggled, settings, &Settings::SetStopAtZLimit);

	// CrossfeedAt
	connect(settings, &Settings::CrossfeedAtChanged, [this](int value)
			{
		if (ui.crossfeed_at_lv->currentRow() != value) 
		{
			ui.crossfeed_at_lv->setCurrentRow(value);
		} });
	connect(ui.crossfeed_at_lv, &QListWidget::currentRowChanged, settings, &Settings::SetCrossfeedAt);

	connect(settings, &Settings::RepeatAtChanged, [this](int value)
			{
		if (ui.repeat_at_lv->currentRow() != value) 
		{
			ui.repeat_at_lv->setCurrentRow(value);
		} });
	connect(ui.repeat_at_lv, &QListWidget::currentRowChanged, settings, &Settings::SetRepeatAt);

	// jogging
	// connect(ui.jog_x_plus_pb, &QPushtto	{ n::pressed, this, &GrinderMainWindow::onJogXPlu ressed);
	// connect(ui.jog_x_minus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogXMinusPressed);
	// connect(ui.jog_y_plus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogYPlusPressed);
	// connect(ui.jog_y_minus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogYMinusPressed);
	// connect(ui.jog_z_plus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogZPlusPressed);
	// connect(ui.jog_z_minus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogZMinusPressed);

	// connect(ui.jog_x_plus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	// connect(ui.jog_x_minus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	// connect(ui.jog_y_plus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	// connect(ui.jog_y_minus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	// connect(ui.jog_z_plus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	// connect(ui.jog_z_minus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);

	// connect(this, &GrinderMainWindow::jog, motion.get(), &GrinderMotion::onJog);

	// dro
	connect(machine, &Machine::positionChanged, [this](Position value)
			{

				ui.dro_lb_x->setText(formatPosition(value.x, 5));
				ui.dro_lb_y->setText(formatPosition(value.y, 5));
				ui.dro_lb_z->setText(formatPosition(value.z, 5)); });

	connect(this, &GrinderMainWindow::infoMessage, this, &GrinderMainWindow::onInfoMessage);
	connect(this, &GrinderMainWindow::errorMessage, this, &GrinderMainWindow::onErrorMessage);
	connect(this, &GrinderMainWindow::warningMessage, this, &GrinderMainWindow::onWarningMessage);

	std::cout << "Signal connections setup complete" << std::endl;
}

void GrinderMainWindow::onJogPressed(Axis axis, bool direction)
{
	emit jog(axis, direction);
}

void GrinderMainWindow::onEstopClicked()
{
	if (!machine->isEstopActive())
	{
		machine->setEstop(true);
	}
	else
	{
		machine->setEstop(false);
	}
}

void GrinderMainWindow::onEstopChanged(bool isActive)
{
	ui.estop_pb->setChecked(isActive);
}

void GrinderMainWindow::onPowerClicked()
{
	// ui.power_pb->setChecked(isOn);
	// if (isOn)
	// {
	// 	ui.power_pb->setText("Power On");
	// 	ui.power_pb->setStyleSheet("background-color: green; color: white;");
	// }
	// else
	// {
	// 	ui.power_pb->setText("Power Off");
	// 	ui.power_pb->setStyleSheet(""); // Reset to default style
	// }
}

void GrinderMainWindow::onHomedClicked()
{
	// if (isHomed)
	// {
	// 	ui.home_all_pb->setText("Homed");
	// 	ui.home_all_pb->setStyleSheet("color: green;");
	// }
	// else
	// {
	// 	ui.home_all_pb->setText("Not Homed");
	// 	ui.home_all_pb->setStyleSheet("color: red;");
	// }
}

void GrinderMainWindow::onJogReleased()
{
	// if (motion)
	// {
	// 	emit jogStop();
	// }
	// else
	// {
	// 	emit errorMessage("Grinder motion controller not initialized");
	// }
}

void GrinderMainWindow::onJogXPlusPressed()
{
	onJogPressed(Axis::X, true);
}

void GrinderMainWindow::onJogXMinusPressed()
{
	onJogPressed(Axis::X, false);
}

void GrinderMainWindow::onJogYPlusPressed()
{
	onJogPressed(Axis::Y, true);
}

void GrinderMainWindow::onJogYMinusPressed()
{
	onJogPressed(Axis::Y, false);
}

void GrinderMainWindow::onJogZPlusPressed()
{
	onJogPressed(Axis::Z, true);
}

void GrinderMainWindow::onJogZMinusPressed()
{
	onJogPressed(Axis::Z, false);
}

void GrinderMainWindow::onGrindStartStop()
{
	if (isShuttingDown)
	{
		return; // Ignore if shutting down
	}

	// if (motion)
	// {
	// 	if (motion->getIsRunning())
	// 	{
	// 		motion->stop();
	// 		std::cout << "Grind stopped" << std::endl;
	// 	}
	// 	else
	// 	{
	// 		motion->start();
	// 		std::cout << "Grind started" << std::endl;
	// 	}
	// }
	// else
	// {
	// 	emit errorMessage("Grinder motion controller not initialized");
	// }
}

void GrinderMainWindow::initializeGrinderBackend()
{
}

void GrinderMainWindow::closeEvent(QCloseEvent *event)
{
	isShuttingDown = true;

	// Stop the grinder if running
	// if (motion && motion->getIsRunning())
	// {
	// 	motion->stop();
	// }

	event->accept();
}

void GrinderMainWindow::onPositionChanged(const Position &pos)
{
	if (ui.dro_lb_x)
	{
		ui.dro_lb_x->setText(formatPosition(pos.x, 4));
	}
	if (ui.dro_lb_y)
	{
		ui.dro_lb_y->setText(formatPosition(pos.y, 4));
	}
	if (ui.dro_lb_z)
	{
		ui.dro_lb_z->setText(formatPosition(pos.z, 4));
	}
}

QString GrinderMainWindow::formatPosition(double pos, int precision)
{
	return QString::number(pos, 'f', precision);
}

void GrinderMainWindow::onInfoMessage(const QString &message)
{
	std::cout << "Info: " << message.toStdString() << std::endl;
	QMessageBox::information(nullptr, "Info", message);
}

void GrinderMainWindow::onErrorMessage(const QString &message)
{
	QMessageBox::critical(nullptr, "Error", message);
}

void GrinderMainWindow::onWarningMessage(const QString &message)
{
	QMessageBox::warning(nullptr, "Warning", message);
}
