#pragma once

enum class Pin
{
	// limits
	XMin = 0,
	XMax,
	YMin,
	YMax,
	ZMin,
	ZMax,

	// speeds
	XSpeed,
	YSpeed,
	ZSpeed,

	// enable grind features for axis
	EnableX,
	EnableY,
	EnableZ,

	// direction for reverse repeat type
	ZDirection,

	// stop once Z reaches the approaching limit
	StopAtZLimit,

	// start/stop the grind cycle
	IsRunning,

	// depth of cut/stepover
	ZCrossfeed,
	YDownfeed,

	// crossfeed at which X limit, and which repeat type when a Z limit is reached
	CrossfeedAt,
	RepeatAt,

	// request a downfeed immediately at the end of the current cycle
	DownfeedNow,

	// dress cycle pins
	DressStartX,
	DressStartY,
	DressStartZ,
	DressEndX,
	DressEndY,
	DressEndZ,
	DressStepoverX,
	DressStepoverY,
	DressStepoverZ,
	DressWheelRpm,
	DressWheelDia,
	DressPointDia,
	DressOffsetGcode,

	NumPins // This should always be the last item
};