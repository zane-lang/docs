# Zane docs

The "Learn" pages of the Zane website: installing Zane, a first project, a
tour of the language, guides and a command reference, for a reader who knows
another programming language.

The [`website`](https://github.com/zane-lang/website) serves the `docs/`
folder at <https://zane-lang.org/docs>. This `README.md` is not a site page.

## Layout

- Every page lives in `docs/`. A folder's `README.md` is its index: its first
  `#` heading is the folder's title, and its links, in order, are the sidebar
  and the pages that get published. A page that no index links is not
  published.
- A page's title is its first `#` heading, and the paragraph after it is its
  description, so keep that to one plain sentence.
- Links are relative `.md` links. A link into another Zane repository uses its
  `https://github.com/zane-lang/<repo>/blob/main/<path>` URL, which the site
  rewrites to its own page.
- A ```` ```zane ```` block is a whole program, starting `package <name>;`,
  that must build and run; an ```` ```output ```` block right after it is its
  exact output. ```` ```zane fragment ```` is shown only, and
  ```` ```zane error ```` must fail `zane check`, with an optional
  `// error: <text>` first line naming the message.

[`CONTRIBUTING.md`](CONTRIBUTING.md) says how the examples are checked.
