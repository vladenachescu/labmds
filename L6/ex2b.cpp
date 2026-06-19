#include <iostream>
#include <vector>
#include <set>
#include <map>
#include <string>

int main() {
    std::map<std::string, std::vector<std::string>> deps = {
        {"curl",    {"openssl", "nghttp2"}},
        {"openssl", {"zlib", "libcrypt"}},
        {"nghttp2", {"zlib"}},
        {"python",  {"zlib", "libffi", "readline"}},
    };

    std::cout << "Resolving dependencies... \n";
    std::vector<std::string> to_install = {"curl", "python", "vim"};
    std::set<std::string> seen(to_install.begin(), to_install.end());

    // Fix: Using index-based loop instead of range-based for loop.
    // Pushing to `to_install` can reallocate the vector, which invalidates
    // the iterators used by the range-based loop.
    for (size_t i = 0; i < to_install.size(); ++i) {
        std::string pkg = to_install[i];
        if (deps.count(pkg)) {
            for (const auto& dep : deps[pkg]) {
                if (seen.insert(dep).second) {
                    to_install.push_back(dep);
                }
            }
        }
    }

    std::cout << "Packages to install: " << to_install.size() << " packages" << std::endl;
    for (const auto& pkg : to_install) {
        std::cout << "  installing " << pkg << std::endl;
    }
    std::cout << "done." << std::endl;
    return 0;
}
