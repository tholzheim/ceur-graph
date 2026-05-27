// Inline-SVG icon library. Lucide-style stroked paths, 16px default,
// `currentColor` so the icon picks up the colour of the surrounding button.
// Register globally in app.js so any template can use `<icon name="…"/>`.

const PATHS = {
  pencil:
    "M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z",
  trash:
    "M3 6h18 M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6 M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2 M10 11v6 M14 11v6",
  plus: "M12 5v14 M5 12h14",
  x: "M18 6 6 18 M6 6l12 12",
  book:
    "M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z",
  warning:
    "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z M12 9v4 M12 17h.01",
  check: "M20 6 9 17l-5-5",
  chevron: "m6 9 6 6 6-6",
  search:
    "M21 21l-4.35-4.35 M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16z",
  logout:
    "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9",
  undo:
    "M3 7v6h6 M21 17a9 9 0 0 0-15-6.7L3 13",
};

export default {
  name: "Icon",
  props: {
    name: { type: String, required: true },
    size: { type: [Number, String], default: 16 },
  },
  computed: {
    path() {
      return PATHS[this.name] ?? "";
    },
  },
  template: `
    <svg :width="size" :height="size" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round"
         aria-hidden="true" focusable="false">
      <path :d="path" />
    </svg>
  `,
};
