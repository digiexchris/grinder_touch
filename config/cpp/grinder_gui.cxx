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
	setMinimumSize(800, 600);

	ui.setupUi(this);
	loadStyleSheet();
	setupMenus();
	connectSignals();
	try
	{
		// Initialize settings manager
		settingsManager = std::make_unique<SettingsManager>("./grinder_settings.json");

		// Initialize grinder motion controller
		motion = std::make_unique<GrinderMotion>(settingsManager.get());

		// Connect position change signals
		connect(motion.get(), &GrinderMotion::positionChanged, this, &GrinderMainWindow::onPositionChanged);

		// Connect signals for modern Qt6 message handling
		connect(motion.get(), &GrinderMotion::infoMessage, this, &GrinderMainWindow::onInfoMessage);
		connect(motion.get(), &GrinderMotion::errorMessage, this, &GrinderMainWindow::onErrorMessage);
		connect(motion.get(), &GrinderMotion::warningMessage, this, &GrinderMainWindow::onWarningMessage);

		std::cout << "Grinder backend initialized successfully" << std::endl;
	}
	catch (const std::exception &e)
	{
		emit errorMessage(QString("Failed to initialize grinder backend: %1").arg(e.what()));
		throw std::runtime_error("Failed to initialize grinder backend: " + std::string(e.what()));
	}

	if (!m_standaloneMode)
	{
		// Initialize the grinder backend only in LinuxCNC mode
		motion->Start();
	}
	else
	{
		std::cout << "Standalone mode: Skipping LinuxCNC backend initialization" << std::endl;

		// emit infoMessage("Grinder GUI initialized in standalone mode");
	}

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

		if (motion)
		{
			motion->stop();
			motion->cleanup();
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
	// Connect UI buttons
	connect(ui.run_stop_pb, &QPushButton::clicked, this, &GrinderMainWindow::onGrindStartStop);
	connect(ui.quit_pb, &QPushButton::clicked, this, &GrinderMainWindow::onExitClicked);

	// jogging
	connect(ui.jog_x_plus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogXPlusPressed);
	connect(ui.jog_x_minus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogXMinusPressed);
	connect(ui.jog_y_plus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogYPlusPressed);
	connect(ui.jog_y_minus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogYMinusPressed);
	connect(ui.jog_z_plus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogZPlusPressed);
	connect(ui.jog_z_minus_pb, &QPushButton::pressed, this, &GrinderMainWindow::onJogZMinusPressed);

	connect(ui.jog_x_plus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	connect(ui.jog_x_minus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	connect(ui.jog_y_plus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	connect(ui.jog_y_minus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	connect(ui.jog_z_plus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);
	connect(ui.jog_z_minus_pb, &QPushButton::released, this, &GrinderMainWindow::onJogReleased);

	connect(this, &GrinderMainWindow::jog, motion.get(), &GrinderMotion::onJog);

	// Connect own signals to own slots (self-connection)
	connect(this, &GrinderMainWindow::infoMessage, this, &GrinderMainWindow::onInfoMessage);
	connect(this, &GrinderMainWindow::errorMessage, this, &GrinderMainWindow::onErrorMessage);
	connect(this, &GrinderMainWindow::warningMessage, this, &GrinderMainWindow::onWarningMessage);

	std::cout << "Signal connections setup complete" << std::endl;
}

void GrinderMainWindow::onJogPressed(Axis axis, bool direction)
{
	if (motion)
	{
		emit jog(axis, direction);
	}
	else
	{
		emit errorMessage("Grinder motion controller not initialized");
	}
}

void GrinderMainWindow::onJogReleased()
{
	if (motion)
	{
		emit jogStop();
	}
	else
	{
		emit errorMessage("Grinder motion controller not initialized");
	}
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

	if (motion)
	{
		if (motion->getIsRunning())
		{
			motion->stop();
			std::cout << "Grind stopped" << std::endl;
		}
		else
		{
			motion->start();
			std::cout << "Grind started" << std::endl;
		}
	}
	else
	{
		emit errorMessage("Grinder motion controller not initialized");
	}
}

void GrinderMainWindow::initializeGrinderBackend()
{
}

void GrinderMainWindow::closeEvent(QCloseEvent *event)
{
	isShuttingDown = true;

	// Stop the grinder if running
	if (motion && motion->getIsRunning())
	{
		motion->stop();
	}

	event->accept();
}

void GrinderMainWindow::onPositionChanged(const Position &pos)
{
	if (ui.actual_lb_x)
	{
		ui.actual_lb_x->setText(formatPosition(pos.x, 4));
	}
	if (ui.actual_lb_y)
	{
		ui.actual_lb_y->setText(formatPosition(pos.y, 4));
	}
	if (ui.actual_lb_z)
	{
		ui.actual_lb_z->setText(formatPosition(pos.z, 4));
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
