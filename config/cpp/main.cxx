#include "grinder-backend.hxx"
#define UNW_LOCAL_ONLY
#include "backward.hpp"
#include "settings.hxx"
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <cxxabi.h>
#include <iostream>

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

	// std::cerr.setf(std::ios::unitbuf);
	// // signal(SIGINT, signal_handler);
	// signal(SIGTERM, signal_handler);
	// std::set_terminate(uncaught_handler); // uncaught c++ exceptions
	// // signal(SIGSEGV, SIG_DFL); // Let backward handle segfaults
	// // signal(SIGABRT, SIG_DFL); // Let backward handle aborts
	// // signal(SIGPIPE, signal_handler);
	// // signal(SIGQUIT, signal_handler);
	// // signal(SIGSEGV, crash_handler);
	// // signal(SIGABRT, crash_handler);

	// signal(SIGSEGV, error_sig_handler);
	// signal(SIGABRT, error_sig_handler);
	// signal(SIGFPE, error_sig_handler);
	// signal(SIGILL, error_sig_handler);
	// signal(SIGBUS, error_sig_handler);

	// std::cout << "Testing backward address resolution:\n";
	// backward::StackTrace st;
	// backward::Printer printer;
	// st.load_here(5);
	// printer.print(st, std::cout);
	// std::cout << "End of test\n";

	// int *ptr = nullptr;
	// *ptr = 42; // This will crash with SIGSEGV

	try
	{
		settings = new SettingsManager("./grinder_settings.json");

		grinder = new GrinderMotion(settings);
		grinder->Start();
		grinder->monitorState();
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	}
	catch (const std::exception &e)
	{
		std::cerr << "Error: " << e.what() << '\n';
		if (grinder != nullptr)
		{
			grinder->cleanup();
			delete grinder;
		}
		return 1;
	}

	return 0;
}
