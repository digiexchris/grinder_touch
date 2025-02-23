#include "settings.hxx"
#include <iostream>

Settings::Settings(std::string aFilename) : myFilename(aFilename)
{
    LoadFromFile();
}

template <typename T>
void Settings::Set(std::string aKey, T aValue)
{
    mySettings[aKey] = aValue;
}

template <typename T>
T Settings::Get(const std::string &aKey) const
{
    auto it = mySettings.find(aKey);
    if (it == mySettings.end())
    {
        throw std::runtime_error("Setting not found: " + aKey);
    }
    return std::get<T>(it->second);
}

void Settings::LoadFromFile()
{
    try
    {
        std::ifstream ifs(myFilename);
        if (!ifs.is_open())
        {
            return; // File doesn't exist yet, start with empty settings
        }

        rapidjson::IStreamWrapper isw(ifs);
        rapidjson::Document doc;
        doc.ParseStream(isw);

        if (doc.HasParseError())
        {
            throw std::runtime_error("Failed to parse settings file");
        }

        for (auto &m : doc.GetObject())
        {
            std::string key = m.name.GetString();
            if (m.value.IsInt())
            {
                mySettings[key] = m.value.GetInt();
            }
            else if (m.value.IsDouble())
            {
                mySettings[key] = m.value.GetDouble();
            }
            else if (m.value.IsBool())
            {
                mySettings[key] = m.value.GetBool();
            }
            else if (m.value.IsString())
            {
                mySettings[key] = std::string(m.value.GetString());
            }
        }
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error loading settings: " << e.what() << std::endl;
    }
}

void Settings::Save()
{
    rapidjson::Document doc;
    doc.SetObject();
    auto &allocator = doc.GetAllocator();

    for (const auto &[akey, value] : mySettings)
    {
        rapidjson::Value key(akey.c_str(), allocator);
        std::visit([&](const auto &v)
                   {
            using T = std::decay_t<decltype(v)>;
            if constexpr (std::is_same_v<T, int>) {
                doc.AddMember(key, v, allocator);
            } else if constexpr (std::is_same_v<T, double>) {
                doc.AddMember(key, v, allocator);
            } else if constexpr (std::is_same_v<T, bool>) {
                doc.AddMember(key, v, allocator);
            } else if constexpr (std::is_same_v<T, std::string>) {
                doc.AddMember(key, 
                    rapidjson::Value(v.c_str(), allocator).Move(), allocator);
            } }, value);
    }

    std::ofstream ofs(myFilename);
    rapidjson::OStreamWrapper osw(ofs);
    rapidjson::Writer<rapidjson::OStreamWrapper> writer(osw);
    doc.Accept(writer);
}

// Template instantiations
template void Settings::Set<int>(std::string, int);
template void Settings::Set<double>(std::string, double);
template void Settings::Set<bool>(std::string, bool);
template void Settings::Set<std::string>(std::string, std::string);

template int Settings::Get<int>(const std::string &) const;
template double Settings::Get<double>(const std::string &) const;
template bool Settings::Get<bool>(const std::string &) const;
template std::string Settings::Get<std::string>(const std::string &) const;
