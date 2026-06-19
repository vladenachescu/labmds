#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <algorithm>

int main() {
    std::map<std::string, std::vector<int>> gradebook = {
        {"alice",   {90, 85, 92}},
        {"bob",     {78, 88}},
        {"charlie", {95, 70, 80}},
    };

    std::map<std::string, int> averages;
    for (auto it = gradebook.begin(); it != gradebook.end(); ++it) {
        const std::string& name = it->first;
        const std::vector<int>& scores = it->second;
        int sum = 0;
        for (int s : scores) sum += s;
        averages[name] = sum / scores.size();
    }

    // Fix: Copy map entries to a vector to enable sorting by average grade
    std::vector<std::pair<std::string, int>> sorted_averages(averages.begin(), averages.end());
    
    // Sort by value (average grade) descending, or by name if grades are equal
    std::sort(sorted_averages.begin(), sorted_averages.end(), [](const std::pair<std::string, int>& a, const std::pair<std::string, int>& b) {
        if (a.second != b.second) {
            return a.second > b.second; // descending order of grades
        }
        return a.first < b.first; // alphabetical order of names
    });

    std::cout << "Rankings:" << std::endl;
    for (auto it = sorted_averages.begin(); it != sorted_averages.end(); ++it) {
        std::cout << "  " << it->first << ": " << it->second << std::endl;
    }

    return 0;
}
