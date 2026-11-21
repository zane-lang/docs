# Zane docs

The "Learn" pages of the Zane website: installing Zane, a first project, a
tour of the language, guides and a command reference, for a reader who knows
another programming language.

The [`website`](https://github.com/zane-lang/website) serves the `docs/`
folder at <https://zane-lang.org/docs>. This `README.md` is not a site page.

## Layout

- Every page lives in `docs/`. Each folder's `README.md` is that folder's
  index page. The index page's first `#` heading is the folder's title, and
  the index page's links, in order, become the sidebar and decide which pages
  are published. A page that no index page links to is not published.
- The site takes a page's title from its first `#` heading and the page's
  description from the paragraph after that heading, so write that paragraph
  as one plain sentence.
- Links between pages are relative `.md` links. A link to a file in another
  Zane repository uses that file's
  `https://github.com/zane-lang/<repo>/blob/main/<path>` URL, and the site
  rewrites the URL to the site's own page for that file.
- A ```` ```zane ```` block is a whole program, starting `package <name>;`,
  that must build and run. An ```` ```output ```` block right after it holds
  the program's exact output. A ```` ```zane fragment ```` block is shown but
  not run. A ```` ```zane error ```` block must fail `zane check`, and may
  start with a `// error: <text>` line giving text that the compiler's error
  message must contain. A fence with `file=<path>` in its info string, such
  as ```` ```c file=binding.h ````, is a file of the next example's package,
  such as a C source or header.

[`CONTRIBUTING.md`](CONTRIBUTING.md) describes how the examples are checked.
