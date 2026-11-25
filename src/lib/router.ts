import { useSyncExternalStore } from "react";
import { transition } from "./motion";

export type Route =
  | { page: "today" }
  | { page: "atlas"; topic?: string; level?: string; q?: string; view?: string }
  | { page: "learn" }
  | { page: "practice" }
  | { page: "books"; grade?: number; part?: string; unit?: number; index?: number }
  | { page: "me" }
  | { page: "about" }
  | { page: "support" };

export interface Location {
  route: Route;
  /** Word sheet open on top of the route. */
  word: string | null;
}

function parse(hash: string): Location {
  const [path, query = ""] = hash.replace(/^#/, "").split("?");
  const params = new URLSearchParams(query);
  const word = params.get("w");
  const seg = path.split("/").filter(Boolean);
  let route: Route = { page: "today" };
  if (seg[0] === "atlas")
    route = { page: "atlas", topic: params.get("topic") || undefined, level: params.get("level") || undefined, q: params.get("q") || undefined, view: params.get("view") || undefined };
  else if (seg[0] === "learn") route = { page: "learn" };
  else if (seg[0] === "practice") route = { page: "practice" };
  else if (seg[0] === "books")
    route = {
      page: "books",
      grade: params.has("grade") ? Number(params.get("grade")) : undefined,
      part: params.get("part") || undefined,
      unit: params.has("unit") ? Number(params.get("unit")) : undefined,
      index: params.has("index") ? Number(params.get("index")) : undefined,
    };
  else if (seg[0] === "me") route = { page: "me" };
  else if (seg[0] === "about") route = { page: "about" };
  else if (seg[0] === "support") route = { page: "support" };
  else if (seg[0] === "w" && seg[1]) return { route: { page: "atlas" }, word: decodeURIComponent(seg[1]) };
  return { route, word };
}

export function href(route: Route, word?: string | null) {
  const params = new URLSearchParams();
  if (route.page === "atlas") {
    if (route.topic) params.set("topic", route.topic);
    if (route.level) params.set("level", route.level);
    if (route.q) params.set("q", route.q);
    if (route.view) params.set("view", route.view);
  }
  if (route.page === "books") {
    if (route.grade) params.set("grade", String(route.grade));
    if (route.part) params.set("part", route.part);
    if (route.unit) params.set("unit", String(route.unit));
    if (route.index) params.set("index", String(route.index));
  }
  if (word) params.set("w", word);
  const q = params.toString();
  return `#/${route.page === "today" ? "" : route.page}${q ? `?${q}` : ""}`;
}

let loc = parse(location.hash);
const subs = new Set<() => void>();
window.addEventListener("hashchange", () => {
  const next = parse(location.hash);
  const pageChange = next.route.page !== loc.route.page;
  const update = () => {
    loc = next;
    subs.forEach((f) => f());
  };
  // Crossfade between pages; the word sheet animates on its own.
  if (pageChange && !next.word) transition(update);
  else update();
});

export const useLocation = () =>
  useSyncExternalStore(
    (f) => {
      subs.add(f);
      return () => subs.delete(f);
    },
    () => loc,
  );

export function go(route: Route, word?: string | null, replace = false) {
  const h = href(route, word);
  if (replace) history.replaceState(null, "", h);
  else history.pushState(null, "", h);
  const next = parse(h);
  const pageChange = next.route.page !== loc.route.page;
  const update = () => {
    loc = next;
    subs.forEach((f) => f());
  };
  if (pageChange && !replace) transition(update);
  else update();
}

export const openWord = (id: string) => go(loc.route, id);
export const closeWord = () => go(loc.route, null);
export const currentLocation = () => loc;
