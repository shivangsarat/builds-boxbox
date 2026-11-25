## Watching a race, and understanding a race

A television broadcast is good at telling a story. It shows the battle at the front, the pit stops, the incidents and the moments that matter. But there is another perspective I wanted to explore: a view where I could follow an individual driver, inspect their lap history, compare tyre strategies and move through the data at my own pace. That is the idea behind my F1 Telemetry dashboard — my own little pit wall.

This is the first chapter of BoxBox Builds, a record of the product and engineering decisions behind the application. Rather than treating the current interface as the end of the story, I want to examine how the problem changed as the implementation developed. The interesting decisions are often the ones that become visible only after an apparently straightforward feature is put to use.

## The earliest recorded implementation

The earliest main-branch commit is dated 2 October 2026. The repository already contained a TypeScript backend, a data-service module, telemetry processing, a WebSocket handler, and a React frontend with home, race and driver-profile views. That is the beginning of the recorded main-branch history, not necessarily the first day I considered the idea or wrote an uncommitted prototype.

The three views answer different questions. The homepage gives a wider view of the championship and race calendar. The race dashboard brings together information about one session. A driver profile lets the viewer investigate an individual race in more detail. The distinction is important because the data needed for a championship standings table is very different from the data needed to draw a continuous telemetry graph.

The project can therefore be thought of as several related products within one application. A race overview needs to be easy to scan; a driver view needs to support exploration; a live interface needs to keep changing while remaining understandable. These goals create different constraints even when the underlying information comes from related data sources.

## From data retrieval to a viewing experience

A historical request can return a collection of records from a known session. A live feed, on the other hand, may deliver individual updates over time. A user who joins halfway through a session cannot assume that the first event received represents the beginning of the race. That makes the source of information, the derived session state and the user-facing presentation distinct concerns.

```text
Data sources
    ↓
Session processing and state
    ↓
Race overview / driver profile / timeline
```

This is a conceptual model, not a full deployment diagram. It helps explain why the application needs more than a collection of direct requests from a browser. For example, a lap table needs to identify complete laps; a tyre-strategy view needs to relate tyre stints to those laps; a timeline needs to place samples in a meaningful order. Making each page independently responsible for those calculations can create inconsistent interpretations.

The early repository had separate modules for retrieval and processing. Later design conversations explored shared backend calculation logic for historical and live data, with a thinner frontend consuming consistent results. That is a direction recorded in the design discussions, not a claim that every proposed refactor has reached the deployed application.

## The first experiments

The main-branch history records several early changes in quick succession. On 2 October a small development service was added to make an archived race appear current. The next day, changes explored paid data access, request pacing and chart navigation. Later commits addressed WebSocket handling and lap tables.

The sequence is a reminder that a real-time application evolves along several dimensions at once. Making data available is one concern; controlling how much data is retrieved is another. Making the interface useful while that data changes is a third. Progress in any one dimension can expose weaknesses in the others.

A small development simulator, for example, can unblock interface work even before it is realistic enough to exercise connection recovery. A cache can reduce repeated retrieval without making a live stream more reliable. A chart that moves smoothly can still lose its useful historical context when a page is reopened. It is worth discussing those problems separately instead of describing the project as a single rewrite from an old architecture to a new one.

## The constraints that became visible

Several questions emerged in the subsequent development conversations. One involved running the dashboard on four devices while using a single backend process and still seeing API rate-limit warnings. Another concerned the difference between following new samples and manually inspecting previous laps. A third involved the risk of the dashboard displaying information before the television broadcast shows it.

These constraints change how I think about success. More frequent data retrieval is not automatically better if it exhausts the upstream budget. An always-moving graph is not automatically more useful if it prevents comparison. A faster dashboard is not always a better companion to a delayed broadcast. The product is not simply trying to minimize the age of every piece of data; it is trying to deliver the right information in the right context.

There were also questions around retaining live history across navigation and handling reconnects. Those discussions establish problems to investigate. They do not prove that all of those issues have been solved, and the series will distinguish verified changes from proposed improvements.

## A useful way to evaluate the architecture

For each later chapter, I will look at three layers: the product requirement, the implementation decision and the evidence of its outcome. For a real-time feature, that means asking whether the same session is represented consistently across views, whether the amount of upstream work is bounded, and whether the person using the interface can understand what information is current and what information is historical.

Where evidence is incomplete, the right answer is to leave the uncertainty visible. An early commit may tell me what code changed but not why a particular decision was made. A screenshot may demonstrate the current interface but not prove how it behaves during connection loss. A successful request may not establish how the backend behaves with four clients. The blog will separate those forms of evidence rather than treat them as interchangeable.

## The application today

The captured interface shows a championship overview, historical race dashboard, driver profiles, telemetry timelines and tyre information. These are current product views displaying historical race data. They are not screenshots of the October prototype and do not establish live-session availability. The application is accessible at [F1 Telemetry](https://gridlock-f1dash.duckdns.org/).

The next chapter explores an early solution to a very practical constraint: how to test a race dashboard when there is no live race. From there, the series will investigate request coordination and interactive telemetry charts, before returning to other verified decisions and to the evolution of GRIDLOCK.

This is a build journal, not a benchmark or a claim that the architecture is finished. The aim is to document the decisions, the alternatives and the limitations as they become visible — and to show how each of them affects the experience of following a race.
