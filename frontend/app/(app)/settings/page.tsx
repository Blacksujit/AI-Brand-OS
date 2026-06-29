"use client";

import { useState } from "react";
import { Button } from "@/features/ui/Button";

export default function SettingsPage() {
  const [platform, setPlatform] = useState("linkedin");
  const [defaultTone, setDefaultTone] = useState("professional");
  const [maxLength, setMaxLength] = useState(300);

  const handleSave = () => {
    localStorage.setItem(
      "brandos-settings",
      JSON.stringify({ platform, defaultTone, maxLength }),
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure your content generation preferences.
        </p>
      </div>

      <div className="max-w-lg space-y-6">
        <div className="space-y-2">
          <label htmlFor="platform" className="text-sm font-medium">
            Default Platform
          </label>
          <select
            id="platform"
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="linkedin">LinkedIn</option>
            <option value="twitter">Twitter / X</option>
            <option value="medium">Medium</option>
            <option value="newsletter">Newsletter</option>
          </select>
        </div>

        <div className="space-y-2">
          <label htmlFor="tone" className="text-sm font-medium">
            Default Tone
          </label>
          <select
            id="tone"
            value={defaultTone}
            onChange={(e) => setDefaultTone(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="professional">Professional</option>
            <option value="conversational">Conversational</option>
            <option value="thought-leadership">Thought Leadership</option>
            <option value="educational">Educational</option>
          </select>
        </div>

        <div className="space-y-2">
          <label htmlFor="maxLength" className="text-sm font-medium">
            Default Max Length
          </label>
          <input
            id="maxLength"
            type="number"
            min={50}
            max={3000}
            value={maxLength}
            onChange={(e) => setMaxLength(Number(e.target.value))}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <Button onClick={handleSave}>Save Settings</Button>
      </div>
    </div>
  );
}
