import React from 'react';
import './Footnote.css';

const Footnote: React.FC = () => {
    return (
        <footer className="footnote">
            <div className="footnote-content">
                <p className="footnote-text">
                    Disclaimer: This website provides information for educational purposes only and does not constitute investment or financial advice.
                </p>
            </div>
        </footer>
    );
};

export default Footnote;
