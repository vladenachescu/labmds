#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> words;
    std::istringstream stream(text);
    std::string word;
    while (stream >> word) {
        for (auto& c : word) c = std::tolower(c);
        words.push_back(word);
    }
    return words;
}

int main(int argc, char* argv[]) {
    const char* filename = argc > 1 ? argv[1] : "big.txt";
    std::ifstream file(filename);
    if (!file) { std::cerr << "cannot open " << filename << std::endl; return 1; }

    std::string text((std::istreambuf_iterator<char>(file)),
                      std::istreambuf_iterator<char>());

    auto words = tokenize(text);

    // Optimize: Single-pass frequency count using an unordered map (O(N))
    std::unordered_map<std::string, int> counts;
    for (const auto& w : words) {
        counts[w]++;
    }

    // Convert map to a vector for sorting
    std::vector<std::pair<std::string, int>> freqs(counts.begin(), counts.end());

    // Sort to get top 10
    std::partial_sort(freqs.begin(),
        freqs.begin() + std::min<size_t>(10, freqs.size()),
        freqs.end(),
        [](const auto& a, const auto& b) { return a.second > b.second; });

    for (int i = 0; i < 10 && i < (int)freqs.size(); i++) {
        std::cout << freqs[i].first << " " << freqs[i].second << std::endl;
    }
    return 0;
}
