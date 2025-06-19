#include "grinder-backend.hxx"
#define UNW_LOCAL_ONLY
#include "backward.hpp"
#include "settings.hxx"
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <cxxabi.h>
#include <iostream>

#include "linuxcnc/machine.hxx"

// backward::SignalHandling sh({SIGSEGV, SIGABRT, SIGFPE, SIGILL, SIGBUS});

static GrinderMotion *grinder = nullptr;

void signal_handler(int sig)
{
	std::cout << "Signal received: " << sig << "\n";
	if (grinder != nullptr)
	{
		delete grinder;
		grinder = nullptr;
	}
	exit(sig);
}

SettingsManager *settings = nullptr;

int main(int argc, char **argv)
{
	if (argc > 1)
	{
		setenv("INI_FILE_NAME", argv[1], 1);
	}

	std::cerr.setf(std::ios::unitbuf);

	settings = new SettingsManager("./grinder_settings.json");

	// Machine machine;

	// grinder = new GrinderMotion(settings);
	//  grinder->Start();
	//  grinder->monitorState();
	std::this_thread::sleep_for(std::chrono::milliseconds(50));

	return 0;
}
