#pragma once

#include <QEvent>
#include <QString>

class MessageEvent : public QEvent
{
	Q_DECL_EVENT_COMMON(MessageEvent)
public:
	explicit MessageEvent(const QString &message)
		: QEvent(QEvent::Type(QEvent::User + 0)), m_message(message) {}

	QString message() const { return m_message; }

private:
	QString m_message;
};

class ErrorEvent : public MessageEvent
{
	Q_DECL_EVENT_COMMON(ErrorEvent)
	using MessageEvent::MessageEvent;
};

class WarningEvent : public MessageEvent
{
	Q_DECL_EVENT_COMMON(WarningEvent)
	using MessageEvent::MessageEvent;
};

class InfoEvent : public MessageEvent
{
	Q_DECL_EVENT_COMMON(InfoEvent)
	using MessageEvent::MessageEvent;
};