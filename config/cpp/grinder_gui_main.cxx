#include "grinder_gui.hxx"
#include <QApplication>
#include <QDir>
#include <QFile>
#include <QMainWindow>
#include <QMessageBox>
#include <QTimer>
#include <QUiLoader>
#include <QVBoxLayout>
#include <cstdlib>
#include <iostream>

int main(int argc, char *argv[])
{
	QApplication app(argc, argv);

	// Check for standalone mode
	bool standaloneMode = false;
	for (int i = 1; i < argc; i++)
	{
		if (QString(argv[i]) == "--standalone" || QString(argv[i]) == "-s")
		{
			standaloneMode = true;
			std::cout << "Running in standalone mode (no LinuxCNC connection)" << std::endl;
			break;
		}
	}

	if (!standaloneMode)
	{
		// LinuxCNC passes the INI file path as the first argument
		if (argc > 1 && QString(argv[1]) != "--standalone" && QString(argv[1]) != "-s")
		{
			setenv("INI_FILE_NAME", argv[1], 1);
			std::cout << "LinuxCNC INI file: " << argv[1] << std::endl;
		}
		else
		{
			std::cerr << "Warning: No INI file provided, using default" << std::endl;
			setenv("INI_FILE_NAME", "./grinder-sim.ini", 1);
		}
	}

	// try
	// {
	// Create and show the main grinder GUI window
	GrinderMainWindow window(nullptr, standaloneMode);
	window.show();

	return app.exec();
	// }
	// catch (const std::exception &e)
	// {
	// 	QMessageBox::critical(nullptr, "Grinder GUI Error",
	// 						  QString("Failed to start grinder GUI: %1").arg(e.what()));
	// 	std::cerr << "Error: " << e.what() << std::endl;
	// 	return 1;
	// }
}
