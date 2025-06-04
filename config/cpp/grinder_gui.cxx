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

GrinderMainWindow::GrinderMainWindow(QWidget *parent, bool standaloneMode)
	: QMainWindow(parent), m_centralWidget(nullptr), m_tabWidget(nullptr), m_statusTimer(new QTimer(this)), m_grinderMotion(nullptr), m_settingsManager(nullptr), m_isInitialized(false), m_isShuttingDown(false), m_standaloneMode(standaloneMode)
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

	// Load the UI file and setup the interface
	loadUiFile();
	setupWidgetReferences();
	setupMenus();
	connectSignals();

	if (!m_standaloneMode)
	{
		// Initialize the grinder backend only in LinuxCNC mode
		initializeGrinderBackend();

		// Start status updates only in LinuxCNC mode
		startStatusUpdates();
	}
	else
	{
		std::cout << "Standalone mode: Skipping LinuxCNC backend initialization" << std::endl;
	}

	m_isInitialized = true;

	std::cout << "Grinder Touch GUI initialized successfully" << std::endl;
}

GrinderMainWindow::~GrinderMainWindow()
{
	m_isShuttingDown = true;

	if (!m_standaloneMode)
	{
		stopStatusUpdates();

		if (m_grinderMotion)
		{
			m_grinderMotion->stop();
			m_grinderMotion->cleanup();
		}
	}
}

void GrinderMainWindow::loadUiFile()
{
	QUiLoader loader;
	QFile file("grinder_touch.ui");

	if (!file.open(QIODevice::ReadOnly))
	{
		// Try alternative paths
		QStringList searchPaths = {
			"./grinder_touch.ui",
			"../grinder_touch.ui",
			QDir::currentPath() + "/grinder_touch.ui"};

		bool found = false;
		for (const QString &path : searchPaths)
		{
			file.setFileName(path);
			if (file.open(QIODevice::ReadOnly))
			{
				found = true;
				std::cout << "Found UI file at: " << path.toStdString() << std::endl;
				break;
			}
		}

		if (!found)
		{
			throw std::runtime_error("Could not find grinder_touch.ui file");
		}
	}

	QWidget *widget = loader.load(&file, nullptr); // Don't parent to 'this'
	file.close();

	if (!widget)
	{
		throw std::runtime_error("Failed to load UI file: " + loader.errorString().toStdString());
	}

	// Check if the loaded widget is a QMainWindow
	QMainWindow *loadedMainWindow = qobject_cast<QMainWindow *>(widget);
	if (loadedMainWindow)
	{
		// Show the loaded main window directly
		loadedMainWindow->show();

		// For now, just hide our empty window to avoid confusion
		// The user will fix this properly
		hide();

		// Store reference to the loaded window's central widget for widget finding
		m_centralWidget = loadedMainWindow->centralWidget();
		if (!m_centralWidget)
		{
			m_centralWidget = loadedMainWindow; // Use the main window itself if no central widget
		}
	}
	else
	{
		// If it's not a QMainWindow, use it directly as central widget
		setCentralWidget(widget);
		m_centralWidget = widget;
	}

	// Find the main tab widget
	m_tabWidget = widget->findChild<QTabWidget *>("tabWidget");
	if (!m_tabWidget)
	{
		std::cout << "Warning: Could not find main tabWidget in UI file" << std::endl;
		// List all child widgets for debugging
		std::cout << "Available child widgets:" << std::endl;
		const auto children = widget->findChildren<QWidget *>();
		for (const auto *child : children)
		{
			if (!child->objectName().isEmpty())
			{
				std::cout << "  - " << child->objectName().toStdString()
						  << " (" << child->metaObject()->className() << ")" << std::endl;
			}
		}
	}
	else
	{
		std::cout << "Found tabWidget with " << m_tabWidget->count() << " tabs" << std::endl;
	}

	std::cout << "UI file loaded successfully" << std::endl;

	// Load the stylesheet
	loadStyleSheet();
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

void GrinderMainWindow::setupWidgetReferences()
{
	if (!m_centralWidget)
	{
		std::cerr << "Central widget not available for widget reference setup" << std::endl;
		return;
	}

	// Position labels
	m_actualLbX = m_centralWidget->findChild<QLabel *>("actual_lb_x");
	m_actualLbY = m_centralWidget->findChild<QLabel *>("actual_lb_y");
	m_actualLbZ = m_centralWidget->findChild<QLabel *>("actual_lb_z");

	// Override controls
	m_feedOverrideSl = m_centralWidget->findChild<QSlider *>("feed_override_sl");
	m_spindleOverrideSl = m_centralWidget->findChild<QSlider *>("spindle_override_sl");
	m_rapidOverrideSl = m_centralWidget->findChild<QSlider *>("rapid_override_sl");
	m_feedOverrideLb = m_centralWidget->findChild<QLabel *>("feed_override_lb");
	m_spindleOverride0Lb = m_centralWidget->findChild<QLabel *>("spindle_override_0_lb");
	m_rapidOverrideLb = m_centralWidget->findChild<QLabel *>("rapid_override_lb");

	// Jogging controls
	m_jogModesCb = m_centralWidget->findChild<QComboBox *>("jog_modes_cb");
	m_jogVelSl = m_centralWidget->findChild<QSlider *>("jog_vel_sl");
	m_jogVelLb = m_centralWidget->findChild<QLabel *>("jog_vel_lb");
	m_minJogVelLb = m_centralWidget->findChild<QLabel *>("min_jog_vel_lb");
	m_maxJogVelLb = m_centralWidget->findChild<QLabel *>("max_jog_vel_lb");

	// Jog buttons
	m_jogPlusPb0 = m_centralWidget->findChild<QPushButton *>("jog_plus_pb_0");
	m_jogMinusPb0 = m_centralWidget->findChild<QPushButton *>("jog_minus_pb_0");
	m_jogPlusPb1 = m_centralWidget->findChild<QPushButton *>("jog_plus_pb_1");
	m_jogMinusPb1 = m_centralWidget->findChild<QPushButton *>("jog_minus_pb_1");
	m_jogPlusPb2 = m_centralWidget->findChild<QPushButton *>("jog_plus_pb_2");
	m_jogMinusPb2 = m_centralWidget->findChild<QPushButton *>("jog_minus_pb_2");

	// Spindle controls
	m_spindleFwdPb = m_centralWidget->findChild<QPushButton *>("spindle_fwd_pb");
	m_spindleRevPb = m_centralWidget->findChild<QPushButton *>("spindle_rev_pb");
	m_spindleStopPb = m_centralWidget->findChild<QPushButton *>("spindle_stop_pb");
	m_spindleSpeedSb = m_centralWidget->findChild<QSpinBox *>("spindle_speed_sb");
	m_settingsSpeedLb = m_centralWidget->findChild<QLabel *>("settings_speed_lb");

	// Gcode controls
	m_gcodePte = m_centralWidget->findChild<QPlainTextEdit *>("gcode_pte");
	m_optionalStopPb = m_centralWidget->findChild<QPushButton *>("optional_stop_pb");
	m_toolInSpindleLb = m_centralWidget->findChild<QLabel *>("tool_in_spindle_lb");

	// Status displays
	m_taskModeLb = m_centralWidget->findChild<QLabel *>("task_mode_lb");
	m_taskStateLb = m_centralWidget->findChild<QLabel *>("task_state_lb");
	m_motionModeLb = m_centralWidget->findChild<QLabel *>("motion_mode_lb");
	m_interpStateLb = m_centralWidget->findChild<QLabel *>("interp_state_lb");
	m_gcodesLb = m_centralWidget->findChild<QLabel *>("gcodes_lb");
	m_mcodesLb = m_centralWidget->findChild<QLabel *>("mcodes_lb");
	m_errorsPte = m_centralWidget->findChild<QPlainTextEdit *>("errors_pte");
	m_clearErrorsPb = m_centralWidget->findChild<QPushButton *>("clear_errors_pb");

	// Plot widget
	m_plotWidget = m_centralWidget->findChild<QWidget *>("plot_widget");

	// View options
	m_viewDroCb = m_centralWidget->findChild<QCheckBox *>("view_dro_cb");
	m_viewExtentsOptionCb = m_centralWidget->findChild<QCheckBox *>("view_extents_option_cb");
	m_viewToolCb = m_centralWidget->findChild<QCheckBox *>("view_tool_cb");
	m_viewDtgCb = m_centralWidget->findChild<QCheckBox *>("view_dtg_cb");
	m_viewLimitsCb = m_centralWidget->findChild<QCheckBox *>("view_limits_cb");
	m_viewLivePlotCb = m_centralWidget->findChild<QCheckBox *>("view_live_plot_cb");
	m_viewMetricUnitsCb = m_centralWidget->findChild<QCheckBox *>("view_metric_units_cb");
	m_viewOffsetsCb = m_centralWidget->findChild<QCheckBox *>("view_offsets_cb");
	m_viewOverlayCb = m_centralWidget->findChild<QCheckBox *>("view_overlay_cb");
	m_viewVelocityCb = m_centralWidget->findChild<QCheckBox *>("view_velocity_cb");
	m_viewProgramCb = m_centralWidget->findChild<QCheckBox *>("view_program_cb");
	m_viewRapidsCb = m_centralWidget->findChild<QCheckBox *>("view_rapids_cb");

	std::cout << "Widget references setup complete" << std::endl;
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
	// Connect status timer
	connect(m_statusTimer, &QTimer::timeout, this, &GrinderMainWindow::updateStatus);

	// Connect override sliders
	if (m_feedOverrideSl)
	{
		connect(m_feedOverrideSl, &QSlider::valueChanged, this, &GrinderMainWindow::onFeedOverrideChanged);
	}
	if (m_spindleOverrideSl)
	{
		connect(m_spindleOverrideSl, &QSlider::valueChanged, this, &GrinderMainWindow::onSpindleOverrideChanged);
	}
	if (m_rapidOverrideSl)
	{
		connect(m_rapidOverrideSl, &QSlider::valueChanged, this, &GrinderMainWindow::onRapidOverrideChanged);
	}

	// Connect jog controls
	if (m_jogModesCb)
	{
		connect(m_jogModesCb, QOverload<int>::of(&QComboBox::currentIndexChanged),
				this, &GrinderMainWindow::onJogModeChanged);
	}
	if (m_jogVelSl)
	{
		connect(m_jogVelSl, &QSlider::valueChanged, this, &GrinderMainWindow::onJogVelocityChanged);
	}

	// Connect jog buttons
	if (m_jogPlusPb0)
	{
		connect(m_jogPlusPb0, &QPushButton::pressed, [this]()
				{ onJogAxisPlus(0); });
		connect(m_jogPlusPb0, &QPushButton::released, [this]() { /* Stop jog */ });
	}
	if (m_jogMinusPb0)
	{
		connect(m_jogMinusPb0, &QPushButton::pressed, [this]()
				{ onJogAxisMinus(0); });
		connect(m_jogMinusPb0, &QPushButton::released, [this]() { /* Stop jog */ });
	}
	if (m_jogPlusPb1)
	{
		connect(m_jogPlusPb1, &QPushButton::pressed, [this]()
				{ onJogAxisPlus(1); });
		connect(m_jogPlusPb1, &QPushButton::released, [this]() { /* Stop jog */ });
	}
	if (m_jogMinusPb1)
	{
		connect(m_jogMinusPb1, &QPushButton::pressed, [this]()
				{ onJogAxisMinus(1); });
		connect(m_jogMinusPb1, &QPushButton::released, [this]() { /* Stop jog */ });
	}
	if (m_jogPlusPb2)
	{
		connect(m_jogPlusPb2, &QPushButton::pressed, [this]()
				{ onJogAxisPlus(2); });
		connect(m_jogPlusPb2, &QPushButton::released, [this]() { /* Stop jog */ });
	}
	if (m_jogMinusPb2)
	{
		connect(m_jogMinusPb2, &QPushButton::pressed, [this]()
				{ onJogAxisMinus(2); });
		connect(m_jogMinusPb2, &QPushButton::released, [this]() { /* Stop jog */ });
	}

	// Connect spindle controls
	if (m_spindleFwdPb)
	{
		connect(m_spindleFwdPb, &QPushButton::clicked, this, &GrinderMainWindow::onSpindleForward);
	}
	if (m_spindleRevPb)
	{
		connect(m_spindleRevPb, &QPushButton::clicked, this, &GrinderMainWindow::onSpindleReverse);
	}
	if (m_spindleStopPb)
	{
		connect(m_spindleStopPb, &QPushButton::clicked, this, &GrinderMainWindow::onSpindleStop);
	}
	if (m_spindleSpeedSb)
	{
		connect(m_spindleSpeedSb, QOverload<int>::of(&QSpinBox::valueChanged),
				this, &GrinderMainWindow::onSpindleSpeedChanged);
	}

	// Connect error clear button
	if (m_clearErrorsPb)
	{
		connect(m_clearErrorsPb, &QPushButton::clicked, this, [this]()
				{
            if (m_errorsPte) {
                m_errorsPte->clear();
            } });
	}

	std::cout << "Signal connections setup complete" << std::endl;
}

void GrinderMainWindow::initializeGrinderBackend()
{
	try
	{
		// Initialize settings manager
		m_settingsManager = std::make_unique<SettingsManager>("./grinder_settings.json");

		// Initialize grinder motion controller
		m_grinderMotion = std::make_unique<GrinderMotionGui>(m_settingsManager.get());
		m_grinderMotion->Start();

		std::cout << "Grinder backend initialized successfully" << std::endl;
	}
	catch (const std::exception &e)
	{
		throw std::runtime_error("Failed to initialize grinder backend: " + std::string(e.what()));
	}
}

void GrinderMainWindow::startStatusUpdates()
{
	// Update every 50ms for responsive UI
	m_statusTimer->start(50);
}

void GrinderMainWindow::stopStatusUpdates()
{
	m_statusTimer->stop();
}

void GrinderMainWindow::closeEvent(QCloseEvent *event)
{
	m_isShuttingDown = true;

	// Stop the grinder if running
	if (m_grinderMotion && m_grinderMotion->getIsRunning())
	{
		m_grinderMotion->stop();
	}

	stopStatusUpdates();
	event->accept();
}

void GrinderMainWindow::showEvent(QShowEvent *event)
{
	QMainWindow::showEvent(event);

	if (m_isInitialized)
	{
		updateWidgetStates();
	}
}

// Status update methods
void GrinderMainWindow::updateStatus()
{
	if (m_isShuttingDown)
	{
		return;
	}

	updatePositions();
	updateMachineStatus();
	updateGrindStatus();
	updateSpindleStatus();
	updateErrors();
}

void GrinderMainWindow::updatePositions()
{
	// This would be implemented with actual position data from LinuxCNC
	// For now, just placeholder implementation
	if (m_actualLbX)
	{
		m_actualLbX->setText("0.0000");
	}
	if (m_actualLbY)
	{
		m_actualLbY->setText("0.0000");
	}
	if (m_actualLbZ)
	{
		m_actualLbZ->setText("0.0000");
	}
}

void GrinderMainWindow::updateErrors()
{
	// Implementation would check for LinuxCNC errors and display them
}

void GrinderMainWindow::updateMachineStatus()
{
	// Implementation would update machine status displays
}

void GrinderMainWindow::updateGrindStatus()
{
	// Implementation would update grinder-specific status
}

void GrinderMainWindow::updateSpindleStatus()
{
	// Implementation would update spindle status
}

void GrinderMainWindow::updateWidgetStates()
{
	// Update widget states based on current machine state
}

// Placeholder slot implementations
void GrinderMainWindow::onGrindStartStop() { /* Implementation needed */ }
void GrinderMainWindow::onGrindParametersChanged() { /* Implementation needed */ }
void GrinderMainWindow::onDressStartStop() { /* Implementation needed */ }
void GrinderMainWindow::onDressParametersChanged() { /* Implementation needed */ }
void GrinderMainWindow::onGcodeFileOpen() { /* Implementation needed */ }
void GrinderMainWindow::onGcodeRun() { /* Implementation needed */ }
void GrinderMainWindow::onGcodePause() { /* Implementation needed */ }
void GrinderMainWindow::onGcodeStop() { /* Implementation needed */ }
void GrinderMainWindow::onFeedOverrideChanged(int value) { /* Implementation needed */ }
void GrinderMainWindow::onSpindleOverrideChanged(int value) { /* Implementation needed */ }
void GrinderMainWindow::onRapidOverrideChanged(int value) { /* Implementation needed */ }
void GrinderMainWindow::onJogModeChanged() { /* Implementation needed */ }
void GrinderMainWindow::onJogVelocityChanged() { /* Implementation needed */ }
void GrinderMainWindow::onJogAxisPlus(int axis) { /* Implementation needed */ }
void GrinderMainWindow::onJogAxisMinus(int axis) { /* Implementation needed */ }
void GrinderMainWindow::onSpindleForward() { /* Implementation needed */ }
void GrinderMainWindow::onSpindleReverse() { /* Implementation needed */ }
void GrinderMainWindow::onSpindleStop() { /* Implementation needed */ }
void GrinderMainWindow::onSpindleSpeedChanged() { /* Implementation needed */ }
void GrinderMainWindow::onMdiCommand() { /* Implementation needed */ }
void GrinderMainWindow::onMdiHistorySelection() { /* Implementation needed */ }
void GrinderMainWindow::onFileOpen() { /* Implementation needed */ }
void GrinderMainWindow::onFileEdit() { /* Implementation needed */ }
void GrinderMainWindow::onFileReload() { /* Implementation needed */ }
void GrinderMainWindow::onFileQuit() { QApplication::quit(); }
void GrinderMainWindow::onMachineEstop() { /* Implementation needed */ }
void GrinderMainWindow::onMachinePower() { /* Implementation needed */ }
void GrinderMainWindow::onToolEditTable() { /* Implementation needed */ }
void GrinderMainWindow::onToolReloadTable() { /* Implementation needed */ }
void GrinderMainWindow::onViewHalMeter() { /* Implementation needed */ }
void GrinderMainWindow::onViewHalScope() { /* Implementation needed */ }
void GrinderMainWindow::onViewShowHal() { /* Implementation needed */ }

// Helper methods
void GrinderMainWindow::showError(const QString &message)
{
	QMessageBox::critical(this, "Grinder Error", message);
}

void GrinderMainWindow::showInfo(const QString &message)
{
	QMessageBox::information(this, "Grinder Info", message);
}

QString GrinderMainWindow::formatPosition(double pos, int precision)
{
	return QString::number(pos, 'f', precision);
}
