from pathlib import Path


TARGET = Path(r"G:\proj\Decky-send\friendeck\lib\main.dart")


def replace_once(text: str, old: str, new: str, tag: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing block: {tag}")
    return text.replace(old, new, 1)


def main() -> None:
    raw = TARGET.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")

    text = replace_once(
        text,
        """                  Padding(
                    padding: EdgeInsets.fromLTRB(horizontal, 2, horizontal, 4),
                    child: Builder(
                      builder: (context) {
                        final crumbs = _segments(_path);
                        return Align(
                          alignment: Alignment.centerLeft,
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: [
                                for (var i = 0; i < crumbs.length; i++) ...[
                                  TextButton(
                                    onPressed:
                                        (_busy || crumbs[i].path == _path)
                                        ? null
                                        : () => _load(crumbs[i].path),
                                    style: TextButton.styleFrom(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 4,
                                        vertical: 0,
                                      ),
                                      minimumSize: Size.zero,
                                      tapTargetSize:
                                          MaterialTapTargetSize.shrinkWrap,
                                      foregroundColor: scheme.onSurfaceVariant,
                                    ),
                                    child: Text(
                                      crumbs[i].label,
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(
                                            fontWeight: FontWeight.w600,
                                            color: crumbs[i].path == _path
                                                ? scheme.onSurface
                                                : scheme.onSurfaceVariant
                                                      .withValues(alpha: 0.9),
                                          ),
                                    ),
                                  ),
                                  if (i < crumbs.length - 1)
                                    Text(
                                      '/',
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(
                                            color: scheme.onSurfaceVariant
                                                .withValues(alpha: 0.72),
                                          ),
                                    ),
                                ],
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
""",
        """                  Padding(
                    padding: EdgeInsets.fromLTRB(horizontal, 2, horizontal, 4),
                    child: Builder(
                      builder: (context) {
                        final crumbs = _segments(_path);
                        return Container(
                          decoration: BoxDecoration(
                            color: scheme.surfaceContainer,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 4,
                          ),
                          child: Align(
                            alignment: Alignment.centerLeft,
                            child: SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: [
                                  for (var i = 0; i < crumbs.length; i++) ...[
                                    TextButton(
                                      onPressed:
                                          (_busy || crumbs[i].path == _path)
                                          ? null
                                          : () => _load(crumbs[i].path),
                                      style: TextButton.styleFrom(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 10,
                                          vertical: 8,
                                        ),
                                        minimumSize: const Size(0, 40),
                                        tapTargetSize:
                                            MaterialTapTargetSize.padded,
                                        foregroundColor:
                                            scheme.onSurfaceVariant,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            10,
                                          ),
                                        ),
                                      ),
                                      child: Text(
                                        crumbs[i].label,
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall
                                            ?.copyWith(
                                              fontWeight: FontWeight.w600,
                                              color: crumbs[i].path == _path
                                                  ? scheme.onSurface
                                                  : scheme.onSurfaceVariant
                                                        .withValues(alpha: 0.9),
                                            ),
                                      ),
                                    ),
                                    if (i < crumbs.length - 1)
                                      Padding(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 2,
                                        ),
                                        child: Text(
                                          '/',
                                          style: Theme.of(context)
                                              .textTheme
                                              .bodySmall
                                              ?.copyWith(
                                                color: scheme.onSurfaceVariant
                                                    .withValues(alpha: 0.72),
                                              ),
                                        ),
                                      ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
""",
        "breadcrumb bar style",
    )

    TARGET.write_text(text.replace("\n", nl), encoding="utf-8")
    print("patched")


if __name__ == "__main__":
    main()
