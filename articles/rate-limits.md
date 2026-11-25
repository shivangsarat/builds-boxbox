## One backend, several viewers

I was running my Formula 1 dashboard with one backend process and had the application open on four devices. The backend logged rate-limit warnings, including warnings for weekend lap and stint data. That prompted a question about the architecture: if the live feed is shared in the backend, why can additional screens still create pressure on the upstream API?

The answer requires separating the live delivery path from the other information the product needs. A WebSocket connection and a request budget describe different aspects of a distributed application. Counting one does not establish the other.

## Why a shared live connection is not enough

A live dashboard contains several categories of data. Some information changes incrementally, such as driver positions and race events. Other information is requested as a collection, including session metadata, historical laps, weather and tyre stints. A browser may ask for that context when it opens a page or when a user selects a different driver.

A shared upstream subscription can distribute live events to multiple viewers. It cannot automatically consolidate independent HTTP requests triggered by navigation. If four people request the same session, their calls may be eligible to share a result. If they request four different driver histories, at least some of the work may be distinct.

The four-device observation demonstrates an operational symptom. It is not a trace showing exactly which call sites created every warning. Establishing that would require endpoint-level instrumentation and a record of the requests from each client.

## Early changes in the Git history

An early rate-limiting change changed several parts of the then-current implementation. The paid-provider polling interval increased from two seconds to three seconds, retry handling was introduced, session-detail retrieval was staggered and the data-service queue was adjusted to enforce at least 500 milliseconds between request starts.

These are historical code settings, not current provider guarantees or measurements. The live-provider architecture has been explored on multiple branches, so it would be misleading to describe all of the historical polling logic as the deployed live path today.

The currently inspected data-service code has three complementary mechanisms: a cache, an in-flight request map and a promise-based queue. Each solves a different problem.

## Caching: reuse completed work

A valid cached result can satisfy a request without contacting the upstream service. That sounds simple, but the key and lifetime of the cached item are product decisions as much as implementation details.

A session-level result and a driver-level result have different scopes. Leaving a result-affecting parameter out of a key can make unrelated requests share the wrong data. Including irrelevant parameters can prevent equivalent requests from sharing anything at all. A cached historical result may also tolerate a different expiry policy from changing live tyre information.

The key question is which requests represent the same work, and the next question is how long the result remains useful for the person looking at it.

## Coalescing: reuse work already underway

A cache alone does not handle two requests that arrive before the first upstream response is stored. Without a second mechanism, both requests could observe a cold cache and start separate upstream calls.

The inspected data service uses a map of pending promises. When a request arrives for a key that already has an operation in progress, the caller can await that promise. The pending entry is removed in a finally block after the operation settles.

```text
Client A asks for key K → starts upstream request
Client B asks for key K → awaits existing promise
Upstream response       → both callers receive result
```

An illustrative TypeScript sketch, deliberately smaller than the actual implementation:

```typescript
const pending = new Map<string, Promise<unknown>>();
function coalesce(key: string, fetcher: () => Promise<unknown>) {
  const existing = pending.get(key);
  if (existing) return existing;
  const result = Promise.resolve().then(fetcher)
    .finally(() => pending.delete(key));
  pending.set(key, result);
  return result;
}
```

This example omits caching, pacing, retry rules, typing and error policy. It is intended to explain the identity of in-flight work, not to reproduce the full production service.

## Pacing: coordinate distinct requests

Some calls cannot share a response. A queue controls when these distinct operations start rather than pretending that they are identical.

The inspected data-service implementation serializes operations through a promise chain and enforces a minimum spacing of 500 milliseconds between starts. A 429 response triggers a delayed retry; if retrieval fails, the service can return cached data or an empty result.

There is a trade-off here. Pacing creates waiting time, especially when a new view requires several separate collections. Returning cached information on failure can be better than presenting no information at all, but the interface must distinguish stale data from current data and unavailable data from a genuinely empty result. Otherwise a technically successful fallback can produce a misleading display.

The queue is a mechanism for coordination within its scope. It does not establish that all upstream calls use the same path, that all rate limits have been eliminated, or that several backend processes would automatically share one in-memory budget. These claims need separate evidence.

## From time-based refreshes to event-based refreshes

In a subsequent conversation about the driver profile, I considered refreshing weekend tyre history when the currently viewed driver leaves the pits. That is a different way of reasoning about freshness: rather than assuming every collection needs a timer, identify a meaningful race event that could invalidate the existing information.

A pit-exit-triggered refresh introduces its own questions. Duplicate or closely spaced events should not create duplicate requests. The historical endpoint may not reflect the new stint immediately. If a request is already pending, it may need to be shared rather than started again. If the application misses the event during a disconnect, a recovery policy may need to retrieve a newer snapshot.

That approach was proposed in the conversation; it is not presented here as verified deployed behaviour. Its value is the shift in reasoning from refreshing everything to deciding what has actually changed.

## What I would measure next

I would instrument requests by logical endpoint and cache key, recording cache hits, coalesced requests, queue wait times, retry counts and upstream failures. I would also measure the time between a user opening a data-heavy page and that page becoming useful. The two metrics describe different parts of the product: provider pressure and viewer experience.

A controlled comparison would open the same view on several clients, then open different driver views. It could reveal whether identical requests are truly shared and whether distinct requests are being paced. The result should be reported with the environment and observation window, not generalized from one run. I do not have a verified measurement of those improvements for this chapter.

The broader lesson is that the upstream budget belongs to the application, not to an individual browser tab. A live feed can be shared while other work is duplicated. Caching, coalescing and pacing provide useful tools, but the architecture needs a clear definition of which information is shared, which is unique and which should be refreshed when an event occurs.
