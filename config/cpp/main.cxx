#include "grinder-backend.hxx"
#define UNW_LOCAL_ONLY
#include "settings.hxx"
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <cxxabi.h>
#include <iostream>
#include <libunwind.h>

static GrinderMotion *grinder = nullptr;

void print_stacktrace(void)
{
	unw_cursor_t cursor;
	unw_context_t context;

	unw_getcontext(&context);
	unw_init_local(&cursor, &context);

	while (unw_step(&cursor) > 0)
	{
		unw_word_t offset, pc;
		char sym[256];

		unw_get_reg(&cursor, UNW_REG_IP, &pc);
		if (pc == 0)
		{
			break;
		}

		char *name = sym;
		if (unw_get_proc_name(&cursor, sym, sizeof(sym), &offset) == 0)
		{
			int status;
			char *demangled = abi::__cxa_demangle(sym, nullptr, nullptr, &status);
			if (demangled)
			{
				name = demangled;
			}
			std::cerr << "0x" << std::hex << pc << ": " << name << "+0x" << std::hex << offset << std::dec << "\n";
			if (demangled)
			{
				free(demangled);
			}
		}
		else
		{
			std::cerr << "0x" << std::hex << pc << ": -- symbol not found --\n";
		}
	}
}

void crash_handler(int sig)
{
	std::cerr << "Caught signal " << sig << " (" << strsignal(sig) << ")\n";
	print_stacktrace();
	signal(sig, SIG_DFL);
	raise(sig);
}

void signal_handler(int sig)
{
	std::cout << "Signal received: " << sig << "\n";
	if (grinder != nullptr)
	{
		grinder->cleanup();
		delete grinder;
		grinder = nullptr;
	}
	exit(sig);
}

Settings *settings = nullptr;

int main(int argc, char **argv)
{
	if (argc > 1)
	{
		setenv("INI_FILE_NAME", argv[1], 1);
	}

	signal(SIGINT, signal_handler);
	signal(SIGTERM, signal_handler);
	signal(SIGPIPE, signal_handler);
	signal(SIGQUIT, signal_handler);
	signal(SIGSEGV, crash_handler);
	signal(SIGABRT, crash_handler);

	try
	{
		settings = new Settings("grinder_settings.json");

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
