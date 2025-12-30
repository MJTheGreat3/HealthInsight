import React, { useState, useEffect } from 'react';
import './UploadSplashScreen.css';

const UploadSplashScreen = () => {
    const [currentStage, setCurrentStage] = useState(0);
    const [progress, setProgress] = useState(0);

    const stages = [
        {
            icon: (
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M11 16V7.85l-2.6 2.6L7 9l5-5l5 5l-1.4 1.45l-2.6-2.6V16zm-5 4q-.825 0-1.412-.587T4 18v-3h2v3h12v-3h2v3q0 .825-.587 1.413T18 20z" /></svg>
            )
            ,
            text: 'Uploading...',
            subtext: 'Securing your medical document',
            duration: 5000
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><g fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11.5" cy="11.5" r="9.5" /><path strokeLinecap="round" d="M18.5 18.5L22 22" /></g></svg>
            ),
            text: 'Processing...',
            subtext: 'Extracting text from medical report',
            duration: 20000
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" /></svg>
            ),
            text: 'Analyzing...',
            subtext: 'Identifying test results and values',
            duration: 30000
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z" /></svg>
            ),
            text: 'AI analysis...',
            subtext: 'Generating medical insights',
            duration: 25000
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" /></svg>
            ),
            text: 'Finalizing...',
            subtext: 'Preparing your report visualization',
            duration: 5000
        }
    ];

    useEffect(() => {
        let progressInterval;
        let stageAdvanceTimeout;

        const advanceProgress = () => {
            progressInterval = setInterval(() => {
                setProgress(prev => {
                    const newProgress = prev + 1.5;
                    if (newProgress >= 100) {
                        clearInterval(progressInterval);
                        return 100;
                    }
                    return newProgress;
                });
            }, 800);
        };

        const advanceStage = () => {
            stageAdvanceTimeout = setTimeout(() => {
                setCurrentStage(prev => {
                    if (prev < stages.length - 1) {
                        advanceStage(); // Schedule next stage
                        return prev + 1;
                    }
                    return prev;
                });
            }, 12000); // Advance stage every 12 seconds
        };

        advanceProgress();
        advanceStage();

        return () => {
            if (progressInterval) clearInterval(progressInterval);
            if (stageAdvanceTimeout) clearTimeout(stageAdvanceTimeout);
        };
    }, []);

    const currentStageData = stages[Math.min(currentStage, stages.length - 1)];

    return (
        <div className="upload-splash">
            <div className="splash-container">
                <div className="splash-content">
                    {/* Animated medical icon */}
                    <div className="medical-icon">
                        <div className="icon-animation">
                            {currentStageData.icon}
                        </div>
                    </div>

                    {/* Stage text */}
                    <div className="stage-text">
                        <h2>{currentStageData.text}</h2>
                        <p>{currentStageData.subtext}</p>
                    </div>

                    {/* Progress bar */}
                    <div className="progress-container">
                        <div className="progress-bar">
                            <div
                                className="progress-fill"
                                style={{ width: `${Math.min(progress, 100)}%` }}
                            />
                        </div>
                        <span className="progress-text">
                            {Math.min(progress, 100)}%
                        </span>
                    </div>

                    {/* Processing dots animation */}
                    <div className="processing-dots">
                        <div className="dot"></div>
                        <div className="dot"></div>
                        <div className="dot"></div>
                    </div>

                    {/* Stage indicators */}
                    <div className="stage-indicators">
                        {stages.map((stage, index) => (
                            <div
                                key={index}
                                className={`stage-dot ${index <= currentStage ? 'active' : ''} ${index < currentStage ? 'completed' : ''}`}
                            >
                                <span className="stage-icon">{stage.icon}</span>
                            </div>
                        ))}
                    </div>

                    {/* Estimated time */}
                    {/* <div className="time-estimate"> */}
                    {/*     <p>Estimated time remaining: {Math.max(90 - (progress * 0.9), 0)} seconds</p> */}
                    {/* </div> */}
                </div>

                {/* Background decoration */}
                <div className="splash-background">
                    <div className="floating-shape shape-1"></div>
                    <div className="floating-shape shape-2"></div>
                    <div className="floating-shape shape-3"></div>
                </div>
            </div>
        </div>
    );
};

export default UploadSplashScreen;
