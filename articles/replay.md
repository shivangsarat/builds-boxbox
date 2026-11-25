## The event is not always available

A live race dashboard has an awkward development dependency: the event it is designed for does not happen whenever I want to work on the code. Between race weekends, it is easy to build an interface for archived results but harder to exercise an application that believes a session is happening right now. One of the first recorded experiments in my F1 Telemetry project addressed that problem with a development server that made an archived race appear current.

The distinction matters. I was not attempting to reproduce every event in a race perfectly in this first implementation. I was trying to make parts of the product testable without relying entirely on the race calendar.

## The early implementation

The first main-branch commit, dated 2 October 2026, already contained a backend, frontend, telemetry processing, live delivery and several race-specific views. Later that day, the “mock live and ui upgrades” commit introduced a development package called the F1 Time Machine. The application's data-source configuration could direct requests through that service rather than the usual upstream endpoints.

The service selected an archived 2024 Baku race. Requests for the special latest-session identifier were mapped to that session, while session dates were shifted relative to the development server's clock. For session-list responses, the target race received a simulated start and end time. The development service also cached downloaded records in memory and limited some car-data and position responses to the last 120 records.

The choice of historical records was practical: they already provide domain structure, including drivers, sessions, positions and car-data samples. A test double can expose familiar response shapes while changing the temporal context in which the application sees them.

## How the adapter fitted into the application

```text
Archived race records
          ↓
Development adapter
  • remap latest session
  • shift session dates
  • cache responses
          ↓
Existing application data layer
          ↓
Dashboard and driver views
```

This conceptual diagram describes the early HTTP adapter, not the complete production system. The important decision is that it intervened at the data boundary. The application could request the kinds of records it already understood, instead of introducing an entirely separate UI that would only work with invented fixtures.

A simplified example illustrates the separation. This is pseudocode, not a full source listing:

```typescript
function resolveSession(requested: string, archived: string) {
  return requested === 'latest' ? archived : requested;
}
```

Resolving the session identity is only one step. The development adapter still needs to decide what records the application receives, when they become visible and how errors are represented.

## What it unlocked — and what it did not

A historical results page knows a session has completed. A live page may change its behaviour when the session starts, ends or is in progress. The home view can show a live-session entry point; the race view can choose different presentation and retrieval paths. Reinterpreting an archived session's dates gives an early implementation a way to exercise some of those decisions.

A cached historical response is still a snapshot, however. Moving the session dates does not make the underlying records arrive at their original rate. Returning the last 120 samples is not equivalent to playing a stream of events as race time progresses. The first Time Machine was an adapter using historical responses, not a complete event-time replay engine.

This creates a subtle risk. If the mock exposes information from the entire session regardless of its simulated clock, the application might be able to see information that would not yet have existed at that instant. A test of live-state logic would then pass for the wrong reason. A more complete replay must define which records are visible at each simulated time, including how requests for historical context interact with that boundary.

## How a more realistic replay could evolve

I would separate the event archive, the simulation clock and the delivery adapter. The archive should contain stable records; the clock should determine which records are eligible for delivery; and the adapter should expose them through the same interfaces expected by the application.

That separation would make it possible to run the same test repeatedly. A normal-speed playback could reveal issues that only appear during realistic pacing. An accelerated playback could shorten the feedback loop. A paused clock would make it easier to inspect a specific intermediate state. None of those capabilities should be inferred from the initial adapter simply because the package was called a time machine.

There is also an ordering distinction. Event time describes when something happened; delivery time describes when the application received it. A realistic test environment might deliver an older record after a newer one, duplicate an event or temporarily stop delivering updates. Those conditions help test whether a state reducer and client view behave correctly when the network is imperfect.

## The tests I would prioritize

The first category is lifecycle behaviour: the session changes from not started to live, then to complete. The application should choose the correct view and avoid treating a historical session as a live one merely because a URL contains a particular identifier.

The second category is joining in progress. A viewer should receive enough context to understand the current session without assuming that the live feed begins at lap one. The third category is recovery: after a disconnect, the system should know how to reconstruct its state, which information can be safely reused and which needs to be fetched again.

Finally, a multi-client test would examine whether several viewers watching the same simulated race create duplicated upstream work. This is especially important when the development adapter itself caches records, because a test using the mock might conceal the cost of fetching those records from the actual provider. The simulator needs to test the behaviour being investigated, not hide it.

These are proposed test priorities, not claims that the original Time Machine implemented them. Later mock-live work deserves its own source-backed chapter.

## The trade-off between realism and speed

A comprehensive simulation environment takes time to build and maintain. An early product experiment does not necessarily need that investment. The practical question is what fidelity is required to answer the immediate engineering question. If the question is whether a navigation path works, changing the apparent session dates may be enough. If the question is whether late and out-of-order events corrupt session state, a static response is not enough.

The lesson I take from this early experiment is that test infrastructure can evolve alongside the product. Start by substituting the part of the real world that prevents development, then improve the fidelity as the application's requirements become more demanding. Be explicit about the boundary of the simulation so a convenient fixture is not mistaken for production evidence.

The visual accompanying this chapter uses the current application displaying a historical session and an illustrative flow. It does not depict the original Baku mock server running. The next chapter examines a different constraint that appeared early in the project: coordinating requests against an upstream API budget.
