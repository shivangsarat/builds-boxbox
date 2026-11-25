## A graph that follows the race, and a graph that answers a question

A live chart is usually expected to show the latest information. But when I am following an individual driver in my F1 Telemetry dashboard, I do not always want to look at the latest sample. I might want to investigate the previous lap, inspect a braking zone or compare a portion of the timeline while the race continues.

If every incoming sample moves the visible chart back to the newest point, the investigation becomes frustrating. If the data stops updating whenever the user scrolls back, returning to the latest lap becomes another problem. The product needs to support two different activities: monitoring and investigation.

## How the early graphs evolved

A graph-related commit on 3 October 2026 experimented with reducing the visible chart window from three laps to two, changed its initial maximum position and introduced legend values that could be updated when the cursor selected a point.

These changes show that chart navigation was already a concern early in the project. The amount of information visible at once, the initial viewport and the values available without active cursor interaction all affect whether a user can make sense of the visualization.

The currently inspected main-branch driver profile has a three-lap viewport again. It uses separate state for automatic scrolling, a manually selected minimum position and the latest lap-based position. It contains two telemetry plots, one for speed and engine RPM, and another for driver inputs and gear. The history reviewed here does not establish why the visible window changed again, so I would treat the change itself as evidence and leave the motivation open.

## Separating the timeline from the window

The distinction can be expressed in three layers:

```text
Incoming telemetry samples
            ↓
Lap-based timeline and latest known position
            ↓
Selected visible chart window
```

A sample's location on the timeline belongs to the data. The viewport belongs to the viewer's interaction with that data. A new sample arriving on lap 30 should not inherently force a viewer inspecting lap 12 to change the selected window. Conversely, switching back to automatic following should not require the application to pretend that the selected historical lap is the current lap.

The two concepts can be represented separately in state. The latest known position is derived from available telemetry; automatic following is a viewing preference; the selected minimum position describes where manual exploration begins. This separation is useful even in a historical session where the user is moving through existing data rather than watching a live stream.

## How the inspected implementation chooses its window

If the available data does not fill the initial viewport, the current driver profile uses a fixed starting range. When automatic following is enabled and enough samples exist, it places the latest known position at about 75 percent of the visible range. The remaining space provides room for the next data points. Both chart instances receive the same minimum and maximum so their x-axes represent the same interval.

When manual mode is enabled, the manually selected minimum determines the displayed range. An illustrative version of the viewport calculation is:

```typescript
const width = 3;
function view(latest: number, follow: boolean, manualMin: number) {
  if (latest <= width) return [0, width];
  const min = follow ? latest - width * 0.75 : manualMin;
  return [min, min + width];
}
```

This is simplified explanatory code based on the inspected window logic, not a complete implementation. The actual profile also manages chart instances, cursor values, a slider and lap selections. Selecting a lap in the lap-history table changes the manual position and turns off automatic following. That links a familiar racing concept — a lap number — to a chart location.

## Why lap-based navigation is useful

A raw timestamp is a useful representation inside a data pipeline. A racing viewer may instead think about lap numbers, sectors, pit stops and stints. Expressing the x-axis in lap-based units can make the interaction more intuitive, particularly when the chart is combined with a lap-history table.

The representation is not free of complexity. Comparing drivers across a race requires a consistent definition of progress, and incomplete laps, pit-lane activity and missing records can complicate the mapping. The article focuses on navigating an individual driver's timeline, rather than claiming that the broader cross-driver comparison problem has been solved.

There is a related presentation problem: a legend, selected lap or cockpit value can refer to different positions on the timeline. A user should be able to tell whether a displayed speed refers to the cursor position or the latest sample. If a value changes meaning silently, the graph can be technically accurate but difficult to interpret.

## A stable viewport does not guarantee retained history

In a later design conversation, I reported that information could be lost when navigating from a driver profile to the race page and returning to the driver, even during a live session. I also requested that position and lap-time graphs keep updating without being tied to automatic scrolling.

These observations suggest two distinct engineering problems. The viewport determines which part of the available data is visible. Data retention determines whether that data is still available at all. A stable selected range cannot help if the records behind it disappear when the page component is destroyed.

One possible architecture is to keep session-scoped data outside the lifecycle of individual view components. The view then owns its selected range and presentation preferences, while a shared data layer owns the records and their session identity. Depending on the provider's capabilities and memory constraints, recovery could use a bounded in-memory history, a historical backfill, or a combination of both.

This is a proposed architectural direction. It is not a claim that the reported cross-page history-loss issue has been resolved in the deployed application. The subsequent history-retention and recovery branches need separate examination.

## How I would test the interaction

A useful test starts in automatic mode and advances the latest known position. Both plots should move together. Next, select an earlier lap, advance the data again and verify that the viewing range stays where it was. Returning to automatic mode should jump to the latest available interval without requiring a page reload.

Another test would navigate away and return. It should distinguish loss of the selected viewing range from loss of telemetry records. Those are separate failures, even if both make the page appear to have forgotten its earlier state. A recovery test would simulate a disconnect and compare the state before and after a reconnection.

These tests describe desired behaviour, not completed test results. The current product screenshot shows the interface with historical data, and the inspected source demonstrates the viewport mechanism. Neither alone proves the full live lifecycle works under all conditions.

## The lesson

A chart is not simply the output of a pipeline; it is a tool for asking questions about the data. The most useful live experience may keep receiving new information while allowing the person using it to focus on something that happened earlier. Separating the data from the viewport makes it easier to reason about that experience.

The same principle applies to observability, industrial telemetry and other time-series interfaces. Monitoring and investigation are related activities, but they should not be forced to use the same interaction state. That is the product decision behind the chart, and the reason the next layer of work concerns the lifecycle of the underlying session data rather than merely its visual styling.
