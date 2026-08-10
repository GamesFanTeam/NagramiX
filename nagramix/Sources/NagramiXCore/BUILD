load("@build_bazel_rules_swift//swift:swift.bzl", "swift_library")

swift_library(
    name = "NagramiXCore",
    module_name = "NagramiXCore",
    srcs = glob([
        "Sources/**/*.swift",
    ]),
    copts = [
        "-warnings-as-errors",
    ],
    visibility = [
        "//visibility:public",
    ],
)
